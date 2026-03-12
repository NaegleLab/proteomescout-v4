from app.config import settings
from app.utils import crypto
from proteomescout_worker.helpers import upload_helpers
import urllib.parse
import urllib.request
import urllib.error
import re
import logging
import os
import traceback
import mmap
from Bio import SeqIO, SeqFeature


# returns a reference to the ptmscout logger object
log = logging.getLogger('ptmscout')

uniprot_url = 'https://www.uniprot.org/uniprot/?'
uniprot_batch_url = 'https://www.uniprot.org/uploadlists/'

# invoked by get_uniprot_records
def get_isoform_map(accs):
    isoform_map = {}
    new_accs = set()
    
    for acc in accs:
        m = re.match("^([A-Za-z0-9]+)\-([0-9]+)$", acc.strip())
        if m:
            root = m.group(1)
            isoform = int(m.group(2))

            requested_isoforms = isoform_map.get(root, set())
            requested_isoforms.add(isoform)
            isoform_map[root] = requested_isoforms
            new_accs.add(root)
        else:
            new_accs.add(acc)
            
    return list(new_accs), isoform_map

# invoked by get_uniprot_records
def save_accessions(accs):
    # os needs to be imported
    # tmpfile = os.path.join(settings.ptmscout_scratch_space, crypto.randomString(10))
    # ptmscout_scratch_space is a variable in settings.sample.py which we replace with its value "/tmp" here
    # the randomString function originally located in the crypto.py file has been moved to this file, theerfore the suffix crypto is no longer needed
    tmpfile = os.path.join(settings.ptmscout_scratch_space, crypto.randomString(10))
    with open(tmpfile, 'w') as accfile:
        accfile.write('\n'.join(accs))
    return open(tmpfile)

# invoked by __query_for_isoforms
def save_fasta(fasta):
    tmpfile = os.path.join(settings.ptmscout_scratch_space, crypto.randomString(10))
    with open(tmpfile, 'w') as accfile:
        accfile.write(fasta)
    return open(tmpfile)    

# invoked by __query_for_isoforms
def parse_name(name):
    m = re.match('sp\|([A-Z0-9\-]+)\|(.*)', name)
    
    if m:
        return m.group(1)

# invoked by __query_for_isoforms    
def parse_isoform_number(acc):
    m = re.search("^([A-Za-z0-9]+)\-([0-9]+)$", acc.strip())
    if m:
        return m.group(1), int(m.group(2))
    
    return acc, 0

# invoked by __query_for_isoforms
def parse_description(desc):
    m = re.search("[Ii]soform \S+", desc)
    if m:
        return m.group(0)

MAX_RECORD_PER_ISOFORM_QUERY = 20

# invoked by get_protein_isoforms
def __query_for_isoforms(root_accessions, result_map):
    acc_q = '+OR+'.join([ 'accession:%s' % (k) for k in root_accessions ])
    query = uniprot_url + 'query=%s&format=fasta&include=yes' % (acc_q)
    #result = urllib.request.urlopen(query)
    with urllib.request.urlopen(query) as f:
        response = f.read().decode('utf-8')
    instream = save_fasta(response)
    parsed_result = SeqIO.parse(instream, 'fasta')

    for record in parsed_result:
        # calls parse_description
        name = parse_description(record.description)
        # calls parse_name
        full_acc = parse_name(record.name)
        # calls parse_isoform_number
        root_acc, isoform_number = parse_isoform_number(full_acc)

        if isoform_number > 0:
            result_map[full_acc] = (root_acc, name, isoform_number, str(record.seq).strip().upper())

# invoked by get_uniprot_records
def get_protein_isoforms(root_accessions):
    # Toggle found in settings that is useless for troubleshooting
    # if settings.DISABLE_UNIPROT_QUERY:
    #     return {}

    result_map = {}

    while len(root_accessions) > 0:
        end = min(MAX_RECORD_PER_ISOFORM_QUERY, len(root_accessions))
        query_items = root_accessions[0:end]
        root_accessions = root_accessions[end:]

        # calls on __query_for_isoforms
        __query_for_isoforms(query_items, result_map)

    return result_map

# invoked by parse_xml
def get_scientific_name(name):
    m = re.match("^(.*) \((.*)\)$", name)
    if m != None:
        species = m.group(1).strip()
        parenthetical = m.group(2).strip()

        if parenthetical.find('strain') == 0 or \
                parenthetical.find('isolate') == 0:
            return "%s (%s)" % (species.strip(), parenthetical.strip())
        else:
            return species.strip()

    return name.strip()

# invoked by parse_xml
# returns a list of dictionaries with information regarding mutations
def read_variants(features):
    variant_list = []
    for f in features:
        if f.type == 'sequence variant':
            location = int(f.location.start+1)
            length = int(f.location.end - f.location.start)
            original = None
            mutant = None

            if 'original' in f.qualifiers:
                original = str(f.qualifiers['original']).strip().upper()
            if 'variation' in f.qualifiers:
                mutant = str(f.qualifiers['variation']).strip().upper()

            annotation = ""
            if 'id' in f.qualifiers and 'description' in f.qualifiers:
                annotation = "%s (%s)" % (f.qualifiers['id'], f.qualifiers['description'])
            elif 'id' in f.qualifiers:
                annotation = f.qualifiers['id']
            elif 'description' in f.qualifiers:
                annotation = f.qualifiers['description']
            

            if length == 1 and mutant and len(mutant) == 1:
                mutation_type = 'Substitution (single)'
            elif length > 1 or (mutant and len(mutant) > 1):
                mutation_type = 'Substitution (multiple)'
            else:
                mutation_type = 'Other'

            variant_list.append( {'type':mutation_type, 'location':location,
                                    'original': original, 'mutant':mutant,
                                    'notes':annotation} )
    return variant_list

# invoked by parse_features
def parse_location(location):
    if isinstance(location.start, SeqFeature.UnknownPosition):
        return None, None
    elif isinstance(location.end, SeqFeature.UnknownPosition):
        return location.start.real + 1, None
    else:
        return location.start.real + 1, location.end.real

# VERY IMPORTANT
# invoked by parse_xml
def parse_features(features):
    ignored_features = set(['chain', 'modified residue', 'splice variant', 'mutagenesis site', 'sequence conflict', 'sequence variant', 'glycosylation site' ])
    parsed = []
    for feature in features:
        if feature.type in ignored_features:
            continue

        name = ""
        if 'description' in feature.qualifiers:
            name = feature.qualifiers['description']

        # calls on parse_location
        start, end = parse_location(feature.location)
        if start != None:
            # calls on the ProteinFeatures class originally found in upload_helpers
            # f = upload_helpers.ProteinFeature( feature.type, name, start, end, 'uniprot' )
            f = upload_helpers.ProteinFeature( feature.type, name, start, end, 'uniprot' )
            parsed.append(f)
    return parsed

# invoked by handle_result
def parse_xml(xml):
    name = xml.description
    gene = None

    # calls parse_features
    features = parse_features(xml.features)

    if 'gene_name_primary' in xml.annotations:
        gene = xml.annotations['gene_name_primary']

    locus = xml.name
    taxons = [ t.lower() for t in xml.annotations['taxonomy'] ]
    # calls get_scientific_name
    species = get_scientific_name(xml.annotations['organism'])
#    taxon_id = None

    taxons.append(species.lower())

    other_accessions = [('swissprot', xml.id), ('swissprot', xml.name)]
    if 'gene_name_synonym' in xml.annotations:
        for gene_name in xml.annotations['gene_name_synonym']:
            other_accessions.append(('gene_synonym', gene_name))

    if 'accessions' in xml.annotations:
        for acc in xml.annotations['accessions']:
            rec = ('swissprot', acc)
            if rec not in other_accessions:
                other_accessions.append(rec)

    seq = str(xml.seq).strip().upper()

    # calls on parse_variants which was originally in upload_helpers
    # also calls on read_variants which is native to the file
    # check to see the result of read_variants as this is what is used to create the mutation record
    # should be a list of dictionaries
    variants = read_variants(xml.features)
    # mutations = upload_helpers.parse_variants( xml.id, seq, read_variants(xml.features) )
    mutations = parse_variants( xml.id, seq, variants )

    host_organism = None
    host_organism_taxon_id = None
    if 'organism_host' in xml.annotations:
        host_organism = xml.annotations['organism_host'][0].strip()
    
    # calls on ProteinRecord class originally found in upload_helpers
    pr = upload_helpers.ProteinRecord(name, gene, locus, taxons, species, None, xml.id,
                       other_accessions, features, mutations, seq)

    pr.set_host_organism(host_organism, host_organism_taxon_id)

    return xml.id, pr

# invoked by get_uniprot_records
def handle_result(str_result):
    # try:
    #     str_result = result.read()
    # except httplib.IncompleteRead, e:
    #     str_result = e.partial

    handle = mmap.mmap(-1, len(str_result))
    handle.write(str_result)
    handle.seek(0)

    parsed_result = SeqIO.parse(handle, 'uniprot-xml')

    result_map = {}
    i = 0
    for xml in parsed_result:
        try:
            # calls on parse_xml
            acc, prot_info = parse_xml(xml)
            result_map[acc] = prot_info
        except Exception as e:
            print(traceback.format_exc())
            pass
        i+=1

    return result_map

# invoked by get_uniprot_records
def map_isoform_results(result_map, isoform_map):
    isoforms_by_root = {}

    for iso_acc in isoform_map:
        root_acc, isoform_name, iso_number, iso_seq = isoform_map[iso_acc]

        identified_isoforms = isoforms_by_root.get(root_acc, set())
        isoforms_by_root[root_acc] = identified_isoforms | set([iso_number])

        pr = result_map[root_acc]
      
        isoform_fullname = "%s (%s)" % (pr.name, isoform_name)
        isoform_accs = [('swissprot', iso_acc)]

        # calls on ProteinRecord originally found in upload_helpers
        isoform_pr = upload_helpers.ProteinRecord(isoform_fullname, pr.gene,
                pr.locus, pr.taxonomy, pr.species, pr.taxon_id, iso_acc, isoform_accs, [], [], iso_seq.strip())
        isoform_pr.host_organism = pr.host_organism
        isoform_pr.host_taxon_id = pr.host_taxon_id
        isoform_pr.host_taxonomy = pr.host_taxonomy

        result_map[iso_acc] = isoform_pr

    for root in isoforms_by_root:
        isos = isoforms_by_root[root]
        expected_isos = set( range(1, len(isos)+2) )

        missing_isos = expected_isos - isos
        if len(missing_isos) == 1:
            canonical_isoform = missing_isos.pop()

            new_isoform = "%s-%d" % (root, canonical_isoform)

            isoform_pr = result_map[root]
            isoform_pr.other_accessions.append(('swissprot', new_isoform))

            result_map[root] = isoform_pr
            result_map[new_isoform] = isoform_pr

# invoked by get_uniprot_records
def map_combine(r1, r2):
    return dict(r1.items() + r2.items())

MAX_RETRIES = 5

# NEED to research what rate_limit does and whether it is necessary
# @rate_limit(rate=3)
def get_uniprot_records(accs):
    log.debug("Query: %s", str(accs))
    if settings.DISABLE_UNIPROT_QUERY:
        return []

    # calls on get_isoform_map
    root_accs, isoforms = get_isoform_map(accs)

    i = 0
    while i < MAX_RETRIES:
        try:
            try:
                # calls on save_accessions
                instream = save_accessions(root_accs)
                accessions = instream.read()
                
                params = {
                'from': 'ACC+ID',
                'to': 'ACC',
                'format': 'xml',
                'query': accessions
                }
                
                data = urllib.parse.urlencode(params)
                data = data.encode('utf-8')

                req = urllib.request.Request(uniprot_batch_url, data)

                with urllib.request.urlopen(req) as f:
                    response = f.read()
                
                result_map = handle_result(response)
                # calls on get_protein_isoforms
                isoform_map = get_protein_isoforms(list(isoforms.keys()))

                # calls map_isoform_results
                map_isoform_results(result_map, isoform_map)
                return result_map
            except urllib.error.HTTPError:
                log.debug( "Failed query..." )
                if len(accs) == 1:
                    return {}
                else:
                    bisect = len(accs) / 2
                    r1 = get_uniprot_records(accs[:bisect])
                    r2 = get_uniprot_records(accs[bisect:])

                    # calls on map_combine
                    return map_combine(r1, r2)
        except Exception:
            i+=1
            log.info("Uniprot query failed (retry %d / %d)", i, MAX_RETRIES)

    return {}