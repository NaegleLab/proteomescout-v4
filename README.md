# ProteomeScout (Minimal Flat-File App)

This repository now runs the read-only minimal Flask app only.

## Run

```bash
cd /Users/kmn4mj/GIT/public/proteomescout-v4
conda env create -f environment-minimal.yml
conda activate pscout-minimal
python run_minimal.py
```

Open:

```text
http://127.0.0.1:5000/
```

## Data File Overrides

```bash
PROTEIN_DATA_TSV_PATH=/absolute/path/to/data.tsv \
CITATIONS_TSV_PATH=/absolute/path/to/citations.tsv \
python run_minimal.py
```

## Key Files

- `run_minimal.py` - app entrypoint
- `flatfile_app/` - minimal Flask application
- `requirements-minimal.txt` - minimal pip dependencies
- `environment-minimal.yml` - conda environment spec
- `MINIMAL_SETUP.md` - setup details and VS Code notes