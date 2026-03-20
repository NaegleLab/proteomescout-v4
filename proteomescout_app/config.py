import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'tsv-proteomescout-dev-key')
    DATA_ROOT_DIR = os.environ.get('PROTEOMESCOUT_DATA_DIR', 'data')
    PROTEIN_DATA_TSV_PATH = os.path.join(DATA_ROOT_DIR, 'data.tsv')
    CITATIONS_TSV_PATH = os.path.join(DATA_ROOT_DIR, 'citations.tsv')
    MAX_SEARCH_RESULTS = int(os.environ.get('MAX_SEARCH_RESULTS', '200'))
    # Directory that ProteomeScoutAPI will use to locate (or download) the
    # ProteomeScout flat-file dataset.  The API expects the data files in a
    # "ProteomeScout_Dataset" sub-folder of this directory.
    # Defaults to the same root as the rest of the app data.
    PROTEOMESCOUT_API_DATA_DIR = os.environ.get('PROTEOMESCOUT_API_DATA_DIR', DATA_ROOT_DIR)
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_UPLOAD_BYTES', str(100 * 1024 * 1024)))  # 100 MB
    NAEGLE_LAB_URL = os.environ.get(
        'NAEGLE_LAB_URL',
        'https://engineering.virginia.edu/labs-groups/naegle-research-lab',
    )
    DOCUMENTATION_URL = os.environ.get(
        'DOCUMENTATION_URL',
        'https://www.assembla.com/spaces/proteomescout/wiki/Protein_Viewer',
    )