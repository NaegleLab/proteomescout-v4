# ProteomeScout

This repository runs the read-only TSV-backed ProteomeScout app.

## Python Version

Use Python 3.11.x for local and production environments.
Pin to a 3.11 patch release and avoid automatic minor upgrades (for example, 3.12+) without validation.

## Run

```bash
cd <dir_to_clone>/proteomescout-v4
conda env create -f environment.yml
conda activate pscout
python run.py
```

Open:

```text
http://127.0.0.1:5001/
```

`run.py` defaults to port `5001` to avoid common local conflicts on `5000`.
You can override this with `PORT`, for example:

```bash
PORT=5050 python run.py
```

## Data Directory Configuration
Current location of ProteomeScout Database Files:  [Jan 2026 ProteomeScout on Figshare](https://doi.org/10.6084/m9.figshare.31129045.v1)

```bash
PROTEOMESCOUT_DATA_DIR=/absolute/path/to/directory/with-tsv-files \
python run.py
```

Expected files inside `PROTEOMESCOUT_DATA_DIR`:

- `data.tsv`
- `citations.tsv`

## Key Files

- `run.py` - app entrypoint
- `proteomescout_app/` - Flask application package
- `requirements.txt` - pip dependencies
- `environment.yml` - conda environment spec
- `SETUP.md` - setup details and VS Code notes
