from app.database import protein, taxonomies, modifications, experiment, gene_expression, mutations, uniprot
from app.utils import uploadutils, protein_utils
# from ptmscout.utils import uploadutils, protein_utils
# from ptmscout.config import strings, settings
# from ptmscout.database.modifications import NoSuchPeptide
# from ptmworker.helpers import scansite_tools
from functools import wraps
import logging
# import pickle
import re
# import sys, os
import transaction
import traceback

log = logging.getLogger('ptmscout')

class TaxonError(Exception):
    def __init__(self, taxon):
        self.taxon=taxon

    def __repr__(self):
        return "Unable to locate taxon node: %s" % (self.taxon)

# invoked by uniprot_tools.parse_features
class ProteinFeature(object):
    def __init__(self, tp, name, start, stop, source):
        self.type = tp
        self.name = name
        self.start = start
        self.stop = stop
        self.source = source

# invoked by uniprot_tools.parse_xml and uniprot_tools.map_isoform_results
class ProteinRecord(object):
    def __init__(self, name, gene, locus, taxonomy, species, taxon_id, query_accession, other_accessions, features, mutations, sequence):
        self.name = name
        self.gene = gene
        self.locus = locus

        self.species = species
        self.taxonomy = taxonomy
        self.taxon_id = taxon_id

        self.query_accession = query_accession
        self.other_accessions = other_accessions
        self.features = features
        self.mutations = mutations
        self.sequence = sequence

        self.host_organism = None
        self.host_taxon_id = None
        self.host_taxonomy = []

    def set_host_organism(self, host_species, taxon_id=None):
        self.host_organism = host_species
        self.host_taxon_id = taxon_id

    def set_host_organism_taxonomy(self, taxons):
        self.host_taxonomy = taxons

    def __full_taxonomy(self):
        return self.taxonomy + self.host_taxonomy

    full_taxonomy = property(__full_taxonomy)

    def parse_species(self):
        m = re.match("^(.*) \(((?:strain|isolate) .*)\)$", self.species)

        if m:
            species_root = m.group(1)
            strain = m.group(2)
            return species_root, strain

        return self.species, None

    def copy(self):
        # pr = ProteinRecord(self.name, self.gene, self.locus, self.species,
        #         self.taxon_id, self.query_accession, self.other_accessions[:],
        #         self.features, self.mutations[:], self.sequence)  
        # self.taxonomy was initially missing from the copy constructor
        pr = ProteinRecord(self.name, self.gene, self.locus, self.taxonomy, self.species,
                self.taxon_id, self.query_accession, self.other_accessions[:],
                self.features, self.mutations[:], self.sequence)

        pr.host_organism = self.host_organism
        pr.host_taxon_id = self.host_taxon_id
        pr.host_taxonomy = self.host_taxonomy

        return pr

def notify_job_failed(fn):
    from proteomescout_worker import notify_tasks

    @wraps(fn)
    def ttask(*args, **kwargs):
        try:
            result = fn(*args, **kwargs)
            return result
        except Exception as e:
            job_id = args[-1]
            notify_tasks.notify_job_failed.apply_async((job_id, str(e), traceback.format_exc()))
            raise
    return ttask

def transaction_task(fn):

    @wraps(fn)
    def ttask(*args, **kwargs):
        log.debug("Running task: %s", fn.__name__)
        try:
            result = fn(*args, **kwargs)
            transaction.commit()
            return result
        except:
            log.error(traceback.format_exc())
            transaction.abort()
            raise
    return ttask


def dynamic_transaction_task(fn):

    @wraps(fn)
    def ttask(*args, **kwargs):
        log.debug("Running task: %s", fn.__name__)
        try:
            result = fn(*args, **kwargs)
            transaction.commit()

            if result != None and len(result) == 3:
                new_task, task_args, errback = result
                new_task.apply_async(task_args, link_error=errback )
        except:
            log.error(traceback.format_exc())
            transaction.abort()
            raise
    return ttask

# def summarize_experiment_load(measurements):
#     residues_modified = set()
#     ptms = set()

#     for ms in measurements:
#         for mspep in ms.peptides:
#             residues_modified.add( mspep.peptide.site_type )
#             ptms.add( mspep.modification )

#     final_ptms = set()
#     for ptm in ptms:
#         if ptm is not None:
#             final_ptms.add(ptm)
#             final_ptms |= ptm.getAllParents()

#     return sorted( list( residues_modified ) ), final_ptms

# def find_activation_loops(prot):
#     kinase_domain_names = set([ 'pkinase', 'pkinase_tyr' ])
#     kinase_domains = [ d for d in prot.domains if d.label.lower() in kinase_domain_names ]
#     cutoff_loop_size = 35

#     start_motif = r"D[FPLY]G"
#     stop_motif = r"[ASP][PILW][ED]"

#     i = 0
#     for d in kinase_domains:
#         domain_seq = prot.sequence[d.start-1: d.stop]
#         m1 = re.search(start_motif, domain_seq)

#         if m1 == None:
#             continue

#         domain_seq = domain_seq[m1.end():]
#         m2 = re.search(stop_motif, domain_seq)

#         if m2 == None:
#             continue

#         domain_seq = domain_seq[:m2.start()]

#         loop_start = d.start + m1.end() - 3
#         loop_end = d.start + m1.end() + m2.start() - 1 + 3

#         label = strings.kinase_loop_name if len(domain_seq) <= cutoff_loop_size else strings.possible_kinase_name
#         source = 'predicted'
#/         region = protein.ProteinRegion('Activation Loop', label, source, loop_start, loop_end)

#         i+=1

#         if(not prot.hasRegion(region)):
#             prot.regions.append(region)
#     return i


# def check_ambiguity(measured_pep, species_name):
#     for swissprot in uniprot.findPeptide(measured_pep.peptide, species_name):
#         amb = modifications.PeptideAmbiguity(swissprot.locus, swissprot.accession, measured_pep.id)
#         measured_pep.ambiguities.append(amb)


# def parse_variants(acc, prot_seq, variants):
#     new_mutations = []
    
#     for mutantDict in variants:
#         # for now we're only working with single mutants, but could expand
#         # to double mutants in the future...
#         if(mutantDict['type'] == "Substitution (single)"):
#             new_mutation = mutations.Mutation(mutantDict['type'],
#                     mutantDict['location'], mutantDict['original'],
#                     mutantDict['mutant'], acc, mutantDict['notes'], None)

#             if not new_mutation.consistent(prot_seq):
#                 log.info( "Loaded mutation does not match protein sequence (%d %s) %s -> %s" % (new_mutation.location, prot_seq[new_mutation.location-1], new_mutation.original, new_mutation.mutant) )
#             else:
#                 new_mutations.append(new_mutation)

#     return new_mutations


# def report_errors(exp_id, errors, line_mapping):
#     for e in errors:
#         accession, peptide = line_mapping[e.row]
#         log.warning('Exp %d -- Data file error: %s (%s) -- %s' % (exp_id, peptide, accession, e.msg))
#         experiment.createExperimentError(exp_id, e.row, accession, peptide, e.msg)


def get_strain_or_isolate(species):
    m = re.match(r"^(.*) \(((?:strain|isolate) .*)\)$", species)

    if m:
        species_root = m.group(1)
        strain = m.group(2)
        return species_root, strain

    return species, None


def insert_taxonomic_lineage(species, strain):
    from proteomescout_worker.helpers import entrez_tools

    formatted_species = species
    if strain:
        formatted_species = "%s (%s)" % (species.strip(), strain.strip())

    taxons = entrez_tools.get_taxonomic_lineage( formatted_species )

    parent_taxon = None
    insert_taxons = []
    while parent_taxon == None:
        tx, txid = taxons.pop()
        tx_node = taxonomies.getTaxonomyById(txid)

        if tx_node:
            parent_taxon = tx_node
        else:
            insert_taxons.insert(0, (tx, txid))

    for tx, txid in insert_taxons:
        tx_node = taxonomies.Taxonomy()
        tx_node.parent_id = parent_taxon.node_id
        tx_node.parent = parent_taxon

        tx_node.kingdom = parent_taxon.kingdom
        tx_node.node_id = txid

        if tx == formatted_species:
            tx_node.name = species
            tx_node.strain = strain
        else:
            tx_node.name = tx
            tx_node.strain = None

        tx_node.save()
        parent_taxon = tx_node

    return tx_node

def find_taxon(species, strain):
    tx = taxonomies.getTaxonByName(species, strain=strain)

    if tx == None:
        tx = insert_taxonomic_lineage(species, strain)

#     return tx

# def get_taxonomic_lineage(species):
#     species, strain = get_strain_or_isolate(species)

#     try:
#         taxon = find_taxon(species, strain)
#     except TaxonError:
#         raise uploadutils.ParseError(None, None, "Species: " + species + " does not match any taxon node")

#     taxonomic_lineage = [taxon.formatted_name.lower()]
#     while taxon.parent != None:
#         taxon = taxon.parent
#         taxonomic_lineage.append(taxon.name.lower())

#     taxonomic_lineage.reverse()

#     return taxonomic_lineage

def find_or_create_species(species):
    sp = taxonomies.getSpeciesByName(species)
    
    if(sp == None):
        species_root, strain = get_strain_or_isolate(species)
        
        try:
            tx = find_taxon(species_root, strain)
        except TaxonError:
            raise uploadutils.ParseError(None, None, "Species: " + species + " does not match any taxon node")
        
        sp = taxonomies.Species(species)
        sp.taxon_id = tx.node_id
        sp.save()
        
    return sp


# def create_accession_for_protein(prot, other_accessions):
#     added_accessions = []

#     for db, acc in other_accessions:
#         db = db.lower()
#         if not prot.hasAccession(acc):
#             dbacc = protein.ProteinAccession()
#             dbacc.type = db
#             dbacc.value = acc
#             prot.accessions.append(dbacc)
#             added_accessions.append((db,acc))

#     return added_accessions


# def map_expression_probesets(prot):
#     search_accessions = [ acc.value for acc in prot.accessions ]
#     if prot.acc_gene != '' and prot.acc_gene != None:
#         search_accessions.append(prot.acc_gene)
    
#     probesets = gene_expression.getExpressionProbeSetsForProtein(search_accessions, prot.species_id)
    
#     prot.expression_probes = []
#     prot.expression_probes.extend(probesets)
    
#     log.info("Loaded %d probesets for protein %s | %s", len(probesets), prot.accessions[0].value, str(prot.acc_gene))

# Creates a protein entry
def create_new_protein(name, gene, locus, seq, species):
    """
    Creates a new Protein record

    Parameters
    ----------
    name : str
        The name of the protein
    gene : str
        The gene name associated with the protein
    locus : % str %
        % Need to figure out what this is %
    seq : str
        The sequence of the protein
    species: str
        The species of the protein
        
    Returns
    -------
    prot : Protein
        An instance of a Protein class as defined in protein.py"""
    
    prot = protein.Protein()
    prot.acc_gene = gene
    prot.locus = locus
    prot.name = name
    prot.sequence = seq
    prot.species = find_or_create_species(species)
    prot.species_id = prot.species.id
    return prot

# def get_related_proteins(prot_accessions, species):
#     related_proteins = []
#     for p in protein.getProteinsByAccession(prot_accessions, species):
#         related_proteins.append(p)
#     return related_proteins

# def get_aligned_peptide_sequences(mod_sites, index, pep_seq, prot_seq):
#     upper_case = pep_seq.upper()
#     aligned_peptides = []
    
#     for i in mod_sites:
#         pep_site = i + index
        
#         low_bound = max([pep_site-7, 0])
#         high_bound = min([len(prot_seq), pep_site+8])

# #        pep_tryps   = upper_case[:i] + pep_seq[i] + upper_case[i+1:]
#         pep_aligned = prot_seq[low_bound:pep_site] + pep_seq[i] + prot_seq[pep_site+1:high_bound]
        
#         if pep_site-7 < 0:
#             pep_aligned = (" " * (7 - pep_site)) + pep_aligned
#         if pep_site+8 > len(prot_seq):
#             pep_aligned = pep_aligned + (" " * (pep_site + 8 - len(prot_seq)))
        
#         pep_type = upper_case[i]
        
#         aligned_peptides.append((pep_site+1, pep_aligned, pep_type))
    
#     return aligned_peptides
    

# def check_peptide_matches_protein_sequence(prot_seq, pep_seq):
#     upper_pep = pep_seq.upper()
#     index = prot_seq.find(upper_pep)

#     if index == -1:
#         raise uploadutils.ParseError(None, None, strings.experiment_upload_warning_peptide_not_found_in_protein_sequence)
#     if prot_seq[index+1:].find(upper_pep) > -1:
#         raise uploadutils.ParseError(None, None, strings.experiment_upload_warning_peptide_ambiguous_location_in_protein_sequence)

#     return index

# def get_pep_seq_from_sites(prot_seq, site_designation):
#     site_residues = dict( ( int(s[1:]), s[0] ) for s in site_designation.split(';') )
#     for pos in site_residues:
#         if pos > len(prot_seq):
#             raise uploadutils.ParseError(None, None, "Protein (length %d) does not have site %d" % (len(prot_seq), pos))
#         if site_residues[pos].upper() != prot_seq[pos-1].upper():
#             raise uploadutils.ParseError(None, None, "Designated residue site pair did not match protein sequence %s%d != %s%d" % (site_residues[pos], pos, prot_seq[pos-1], pos))

#     site_positions = set([ int(s[1:]) - 1 for s in site_designation.split(';') ])

#     return "".join( c.lower() if i in site_positions else c for i, c in enumerate(prot_seq.upper()) )

# def get_residue_indicies(pep_seq):
#     modified_alphabet = set("abcdefghijklmnopqrstuvwxyz")
#     return [i for i, r in enumerate( pep_seq ) if r in modified_alphabet ]
    

# def parse_nullmod(prot_seq, pep_seq):
#     pep_seq = pep_seq.strip()
#     index = check_peptide_matches_protein_sequence(prot_seq, pep_seq)
#     residue_indices = get_residue_indicies(pep_seq)
#     aligned_sequences = get_aligned_peptide_sequences(residue_indices, index, pep_seq, prot_seq)
#     return aligned_sequences
    
# def parse_modifications(prot_seq, pep_seq, mods, taxonomy):
#     pep_seq = pep_seq.strip()
#     index = check_peptide_matches_protein_sequence(prot_seq, pep_seq)
#     mod_indices, mod_types = uploadutils.check_modification_type_matches_peptide(None, pep_seq, mods, taxonomy)
#     aligned_sequences = get_aligned_peptide_sequences(mod_indices, index, pep_seq, prot_seq)
    
#     return mod_types, aligned_sequences


# def query_protein_scansite(prot, motif_class):
#     log.info("Loading scansite predictions...")
#     scansite_predictions = scansite_tools.get_scansite_protein_motifs(prot.sequence, motif_class)
    
#     for sp in scansite_predictions:
#         pred = protein.ProteinScansite()
#         pred.score = sp.score
#         pred.percentile = sp.percentile
#         pred.value = sp.nickname
#         pred.source = sp.parse_source()
#         pred.site_pos = int(sp.site[1:])
        
#         if not prot.hasPrediction(pred.source, pred.value, pred.site_pos):
#             prot.scansite.append(pred)

# def get_peptide(prot_id, pep_site, peptide_sequence):
#     upper_pep = peptide_sequence.upper()
#     pep_type = upper_pep[7]
    
#     created = False
#     try:
#         pep = modifications.getPeptideBySite(pep_site, pep_type, prot_id)
#     except NoSuchPeptide:
#         pep = modifications.Peptide()
#         pep.pep_aligned = peptide_sequence
#         pep.site_pos = pep_site
#         pep.site_type = pep_type
#         pep.protein_id = prot_id
#         created = True
    
#     return pep, created
    

# def insert_run_data(MSpeptide, line, units, series_header, run_name, series):
#     for i in range(0, len(series_header)):
#         tp, x = series_header[i]
#         y = None
#         if series[i] != None:
#             y = float(series[i])

#         data = MSpeptide.getDataElement(run_name, tp, x)

#         if data == None:
#             data = experiment.ExperimentData()
#             MSpeptide.data.append(data)

#         data.run = run_name
#         data.priority = i + 1
#         data.type = tp
#         data.units = units
#         data.label = x
#         data.value = y

# def get_series_headers(session):
#     headers = []
#     for col in session.get_columns('data'):
#         headers.append(('data', col.label))
    
#     for col in session.get_columns('stddev'):
#         headers.append(('stddev', col.label))
    
#     return headers



def parse_datafile(session, nullmod=False):
    accessions = {}
    sites_map = {}
    mod_map = {}
    data_runs = {}
    line_mapping = {}
    errors = []
    
    acc_col = session.get_columns('accession')[0]

    pep_col, site_col = None, None
    site_type = None
    pep_cols = session.get_columns('peptide')
    site_cols = session.get_columns('sites')
    if len(pep_cols) > 0:
        pep_col = pep_cols[0]
        site_type = 'peptide'
    if len(site_cols) > 0:
        site_col = site_cols[0]
        site_type = 'sites'
    
    mod_col = None
    if not nullmod:
        mod_col = session.get_columns('modification')[0]
    
    run_col = None
    
    found_cols = session.get_columns('run')
    if found_cols != []:
        run_col = found_cols[0]
    
    data_cols = session.get_columns('data')
    stddev_cols = session.get_columns('stddev')
    
    _, rows = uploadutils.load_header_and_data_rows(session.data_file, float("inf"))
    
    keys = set([])

    line=0
    for row in rows:
        line+=1
        line_errors = uploadutils.check_data_row(line, row, acc_col, pep_col, site_col, mod_col, run_col, data_cols, stddev_cols, keys, not nullmod)

        acc = None
        sites = None
        try:
            acc = row[acc_col.column_number].strip()
            if site_type == 'peptide':
                sites = row[pep_col.column_number].strip()
            if site_type == 'sites':
                sites = row[site_col.column_number].strip()
                try:
                    sites = protein_utils.normalize_site_list(sites)
                except:
                    line_errors.append( uploadutils.ParseError(line, None, "Invalid formatting for sites %s" % (sites)) )
        except IndexError:
            pass

        line_mapping[line] = (acc, sites)

        if len(line_errors) > 0:
            errors.extend(line_errors)
            continue
     
        mods = None
        if not nullmod:
            mods = row[mod_col.column_number].strip()
        
        line_set = accessions.get(acc, [])
        line_set.append(line)
        accessions[acc] = line_set
        
        pep_set = sites_map.get(acc, set())
        pep_set.add(sites)
        sites_map[acc] = pep_set
        
        mod_set = mod_map.get((acc,sites), set())
        mod_set.add(mods)
        mod_map[(acc,sites)] = mod_set

        run_data = data_runs.get((acc, sites, mods), {})
        
        series = []
        for d in data_cols:
            v = row[d.column_number]
            if v != None:
                series.append(v.strip())
            else:
                series.append(v)

        for s in stddev_cols:
            v = row[s.column_number]
            if v != None:
                series.append(v.strip())
            else:
                series.append(v)
            
        if run_col != None:
            run_data[ row[run_col.column_number].strip() ] = (line, series)
        else:
            run_data[ 'average' ] = (line, series)
        
        data_runs[(acc, sites, mods)] = run_data
        
    
    return accessions, sites_map, site_type, mod_map, data_runs, errors, line_mapping
    

# def extract_uniprot_accessions(accessions):
#     uniprot_accs = []
#     other_accs = []
#     for acc in accessions:
#         if(re.search('^[A-NR-Z]\d[A-Z]..\d([\.\-]\d+)?$', acc) != None):
#             uniprot_accs.append(acc)
#         elif(re.search('^[OPQ]\d...\d([\.\-]\d+)?$', acc) != None):
#             uniprot_accs.append(acc)
#         else:
#             other_accs.append(acc)
#     return uniprot_accs, other_accs

# def group_critera(group, arg):
#     if len(group) == 0:
#         return True
#     return group[-1][:6] == arg[:6]


# def create_chunked_tasks_preserve_groups(task_args, MAX_BATCH_SIZE):
#     tasks = []
#     args = []

#     small_groups = [[]]
#     for arg in task_args:
#         if group_critera(small_groups[-1], arg):
#             small_groups[-1].append(arg)
#         else:
#             small_groups.append([arg])

#     for g in small_groups:
#         if len(args) + len(g) <= MAX_BATCH_SIZE:
#             args = args + g
#         else:
#             tasks.append( args )
#             args = g

#     if len(args) > 0:
#         tasks.append( args )

#     return tasks


# def create_chunked_tasks(task_args, MAX_BATCH_SIZE):
#     tasks = []
#     args = []
    
#     for arg in task_args:
#         args.append(arg)
#         if len(args) == MAX_BATCH_SIZE:
#             tasks.append( args )
#             args = []
#     if len(args) > 0:
#         tasks.append( args )
        
#     return tasks
    
# def store_stage_input(exp_id, stage, result):
#     stage = stage.replace(" ", "_")
#     result_path = os.path.join(settings.ptmscout_path, settings.experiment_data_file_path, 'e%d') % (exp_id)
#     if not os.path.exists(result_path):
#         os.mkdir(result_path)
#     result_file = '%s.input' % (stage)

#     writable = open(os.path.join(result_path, result_file), 'w')
#     writable.write(pickle.dumps(result))
#     writable.close()

# def get_stage_input(exp_id, stage):
#     stage = stage.replace(" ", "_")
#     result_path = os.path.join(settings.ptmscout_path, settings.experiment_data_file_path, 'e%d') % (exp_id)
#     result_file = '%s.input' % (stage)

#     file_path = os.path.join(result_path, result_file)
#     if not os.path.exists(file_path):
#         return None

#     readable = open(file_path, 'r')
#     result = pickle.loads(readable.read())
#     readable.close()

#     return result
