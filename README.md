# ProteomeScout

This repository runs the read-only TSV-backed ProteomeScout app.

## Run

```bash
cd <dir_to_clone>/proteomescout-v4
conda env create -f environment.yml
conda activate pscout
python run.py
```

Open:

```text
http://127.0.0.1:5000/
```

## Data File Overrides

```bash
PROTEIN_DATA_TSV_PATH=/absolute/path/to/data.tsv \
CITATIONS_TSV_PATH=/absolute/path/to/citations.tsv \
python run.py
```

## Key Files

- `run.py` - app entrypoint
- `proteomescout_app/` - Flask application package
- `requirements.txt` - pip dependencies
- `environment.yml` - conda environment spec
- `SETUP.md` - setup details and VS Code notes
