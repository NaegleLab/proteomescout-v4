from Bio import Entrez, pairwise2
from app.config import settings
from Bio import Medline
from proteomescout_worker.helpers import pfam_tools, upload_helpers
from proteomescout_worker.geeneus import Proteome
import logging
import re
#from Bio.SubsMat import MatrixInfo
from Bio.Align import substitution_matrices

log = logging.getLogger('ptmscout')

class EntrezError(Exception):
    def __init__(self):
        pass
        
    def __repr__(self):
        return "Unable to fetch protein accession: %s" % (self.acc)



def get_pubmed_record_by_id(pmid):
    Entrez.email = settings.adminEmail
    handle = Entrez.efetch(db="pubmed",id=pmid,rettype="medline",retmode="text")
    records = Medline.parse(handle)
    
    rec_arr = []
    for r in records:
        rec_arr.append(r)

    rval = rec_arr[0] if len(rec_arr) == 1 else None

    if rval != None and 'PG' in rval and rval['PG'].find('-') == -1:
        rval['PG'] = "%s-%s" % (rval['PG'], rval['PG'])

    return rval


def get_taxonomic_lineage(species):
    Entrez.email = settings.adminEmail
    query_species = species.replace(" ", "+").strip()
    search = Entrez.esearch(term = query_species, db="taxonomy", retmode = "xml")
    record = Entrez.read(search)

    if len(record['IdList']) == 0:
        raise upload_helpers.TaxonError(species)

    taxid = record['IdList'][0]
    search = Entrez.efetch(id = taxid, db="taxonomy", retmode = "xml")
    records = Entrez.read(search)

    if len(records) == 0:
        raise upload_helpers.TaxonError(species)

    lineage = [ ( item['ScientificName'], int(item['TaxId']) ) for item in records[0]['LineageEx'] ]

    return lineage + [ (records[0]['ScientificName'], int(taxid)) ]

def map_domain_to_sequence(seq1, domain, seq2):
    domain_seq = seq1[domain.start:domain.stop+1]
    
    new_start = seq2.find(domain_seq)
    
    if new_start == -1:
        return None
    
    new_stop = new_start + len(domain_seq) - 1
    
    new_domain = pfam_tools.PFamDomain()
    new_domain.accession = domain.accession
    new_domain.class_ = domain.class_
    new_domain.label = domain.label
    new_domain.start = new_start
    new_domain.stop = new_stop
    new_domain.p_value = domain.p_value
    new_domain.significant = domain.significant
    new_domain.release = domain.release
    
    return new_domain


def parse_loc(loc):
    m = re.match(r"([0-9]+)\.\.([0-9]+)", loc)
    if m:
        return int(m.group(1)), int(m.group(2))
    
    m = re.match(r"([0-9]+)", loc)
    if m:
        return int(m.group(1)), None

    return 0, None

def parse_protein_features(pxml):
    accepted_features = set(['Region'])
    ignored_names = set(['Splicing variant', 'Variant', 'Mature chain', 'Conflict'])
    parsed_features = []
    for feature in pxml['GBSeq_feature-table']:
        if feature['GBFeature_key'] in accepted_features:
            type = feature['GBFeature_key']
            source = 'ncbi'
            name = get_qualifier('region_name', feature)['GBQualifier_value']

            note_qual = get_qualifier('note', feature)
            if note_qual != None and note_qual['GBQualifier_value'].find('domain') >= 0:
                type = 'Domain'
            if note_qual != None and note_qual['GBQualifier_value'].find('pfam') >= 0:
                continue

            loc = feature['GBFeature_location']
            start, stop = parse_loc(loc)
            if name not in ignored_names:
                f = upload_helpers.ProteinFeature(type, name, start, stop, source)
                parsed_features.append(f)

    return parsed_features

def get_feature(name, table):
    for entry in table:
        if 'GBFeature_key' in entry and entry['GBFeature_key'] == name:
            return entry

def get_qualifier(name, entry):
    if 'GBFeature_quals' in entry:
        for qual in entry['GBFeature_quals']:
            if qual['GBQualifier_name'] == name:
                return qual

def parse_species_name(name):
    m = re.match(r'(.*) \(.*\)', name)
    if m:
        return m.group(1)
    return name

def parse_organism_host(xml):
    source = get_feature('source', xml['GBSeq_feature-table'])
    if source:
        qual = get_qualifier('host', source)
        if qual:
            return parse_species_name(qual['GBQualifier_value']).strip()

def filter_update_other_accessions(other_accessions):
    type_map = {'ref':'refseq', 'gb':'genbank', 'emb': 'embl', 'uniprotkb/swiss-prot':'swissprot', 'swissprot-locus':'swissprot', 'international protein index':'ipi'}
    filtered_accessions = set()
    for tp, value in other_accessions:
        m = re.match('^([a-zA-Z]+)\|(.*)\|$', value)
        gi_re = re.match('^[0-9]+$', value)
        if m:
            tp = m.group(1).lower()
            val = m.group(2)
            if tp in type_map:
                filtered_accessions.add(( type_map[tp], val ))

        elif tp=='GI' and gi_re:
            tp = tp.lower()
            val = "gi|%s" % (value)
            filtered_accessions.add(( tp, val ))
        elif tp.lower() in type_map:
            filtered_accessions.add(( type_map[tp.lower()], value ))
        else:
            filtered_accessions.add(( tp.lower(), value ))
    return list(filtered_accessions)




def get_protein_information(pm, acc):
    seq = pm.get_protein_sequence(acc)
    
    if seq is None:
        e = EntrezError()
        e.acc = acc
        raise e
   
    seq = seq.strip().upper()

    name = pm.get_protein_name(acc)
    gene = pm.get_gene_name(acc)
    taxonomy = [ t.lower() for t in pm.get_taxonomy(acc) ]
    species = pm.get_species(acc).strip()
    taxonomy.append(species.lower())

    locus = None
    rxml = pm.get_raw_xml(acc)
    if 'GBSeq_locus' in rxml:
        locus = rxml['GBSeq_locus']

    prot_accessions = pm.get_other_accessions(acc)
    prot_accessions = filter_update_other_accessions(prot_accessions)

    prot_features = parse_protein_features(pm.get_raw_xml(acc))
    prot_mutations = upload_helpers.parse_variants(acc, seq, pm.get_variants(acc))

    host_organism = None
    try:
        host_organism = parse_organism_host(pm.get_raw_xml(acc))
    except:
        pass

    pr = upload_helpers.ProteinRecord(name, gene, locus, taxonomy, species,
            None, acc, prot_accessions, prot_features, prot_mutations, seq)
    pr.set_host_organism(host_organism)

    return pr

def get_alignment_scores(seq1, seq2):
    #matrix = MatrixInfo.blosum62
    matrix = substitution_matrices.load('BLOSUM62')
    gap_open = -10
    gap_extend = -0.5

    alns = pairwise2.align.globalds(seq1, seq2, matrix, gap_open, gap_extend)
    top_aln = alns[0]
    aln_seq1, aln_seq2, _score, _begin, _end = top_aln
    
    return aln_seq1.count("-"), aln_seq2.count("-") 

def get_proteins_from_ncbi(accessions):
    pm = Proteome.ProteinManager(settings.adminEmail, uniprotShortcut=False)
 
    query_accessions = accessions
    
    log.info("Querying for proteins: %s", str(query_accessions))
    
    pm.batch_get_protein_sequence(query_accessions)

    prot_map = {}
    errors = []
    for acc in query_accessions:
        try:
            prot_map[acc] = get_protein_information(pm, acc)
        except EntrezError as e:
            errors.append(e)
    
    return prot_map, errors
