import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'tsv-proteomescout-dev-key')
    PROTEIN_DATA_TSV_PATH = os.environ.get('PROTEIN_DATA_TSV_PATH', 'data/data.tsv')
    CITATIONS_TSV_PATH = os.environ.get('CITATIONS_TSV_PATH', 'data/citations.tsv')
    MAX_SEARCH_RESULTS = int(os.environ.get('MAX_SEARCH_RESULTS', '200'))
    NAEGLE_LAB_URL = os.environ.get(
        'NAEGLE_LAB_URL',
        'https://engineering.virginia.edu/labs-groups/naegle-research-lab',
    )
    DOCUMENTATION_URL = os.environ.get(
        'DOCUMENTATION_URL',
        'https://www.assembla.com/spaces/proteomescout/wiki/Protein_Viewer',
    )