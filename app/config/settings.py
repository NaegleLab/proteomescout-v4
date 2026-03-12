import os

documentationUrl = "https://www.assembla.com/spaces/proteomescout/wiki"
proteinViewerHelp = "Protein_Viewer"
adminEmail = "proteomescout@seas.wustl.edu"
automailerEmail = "no-reply@seas.wustl.edu"
pubmedUrl = "https://www.ncbi.nlm.nih.gov/pubmed/%d"
issueTrackerUrl = "https://www.assembla.com/spaces/proteomescout/support/tickets"

MINIMUM_PASSWORD_LENGTH = 7

tracking_script = """

"""

accession_urls = {'swissprot':"http://www.uniprot.org/uniprot/%s",
                  'uniprot':"http://www.uniprot.org/uniprot/%s",
                  'entrez_protein':"http://www.ncbi.nlm.nih.gov/protein/%s",
                  'gi':"http://www.ncbi.nlm.nih.gov/entrez/viewer.fcgi?db=protein&amp;id=%s",
                  'refseq':"http://www.ncbi.nlm.nih.gov/entrez/viewer.fcgi?db=protein&amp;id=%s",
                  'GO':"http://amigo.geneontology.org/cgi-bin/amigo/term-details.cgi?term=%s",
                  'genbank':"http://www.ncbi.nlm.nih.gov/entrez/viewer.fcgi?db=protein&amp;id=%s"}

mod_separator_character = ';'
mod_separator_character_alt = '|'
export_address = "app/data/annotate"
naegle_lab_url = 'http://naegle.wustl.edu/'
pfam_family_url = 'http://pfam.sanger.ac.uk/family/'
ptmscout_scratch_space = "/tmp"
experiment_data_file_path = "data/experiments"
export_file_path = "data/export"
annotation_export_file_path = "data/annotate"
pfam_map_file_path = "ptmworker/helpers/pfam.map"
statistics_file = "data/statistics.pyp"
ptmscout_path = "app"
#ptmscout_path = "/data/ptmscout/ptmscout_web"
motif_script_path = os.path.join('scripts', 'motif')

email_regex = r"^[a-zA-Z0-9\.\-\_]+@([a-zA-Z0-9\.\-\_]+\.[a-z]+)$"

DISABLE_PFAM = False
DISABLE_SCANSITE = False
DISABLE_QUICKGO = False
DISABLE_PICR = False
DISABLE_UNIPROT_QUERY = False
DISABLE_DBSNP = False

JOB_AGE_LIMIT = 7 * 86400
REVIEWER_ACCOUNT_EXPIRATION_DAYS = 365

# rate limits in queries per second
SCANSITE_RATE_LIMIT = 3

# email valid domains
valid_domain_suffixes = set([r'.+\.edu',r'.+\.gov', r'icr\.ac\.uk', r'gov\.br', r'.+\.ac\.at'])


isoform_sequence_diff_pfam_threshold = 50



experiment_files_prefix = "experiment_data"
annotation_files_prefix = "annotation_data"
dataset_files_prefix = "dataset_data"


default_mcam_scansite_cutoff = 3
default_mcam_domain_cutoff = 1e-5
default_mcam_p_cutoff = 0.05
mcam_file_path = "data/mcam"

cache_expiration_time = 7 * 86400
cache_storage_directory = "data/cache"
