# App Setup

This setup is for the read-only TSV-backed app in `run.py`.
It is the primary runtime for this repository.

## Python Version

Use Python 3.11.x for development and production deployment.
Prefer patch-level updates within 3.11 and validate before moving to a newer minor version.

## Recommended: conda only

This is the simplest option on macOS ARM because `numpy`, `scipy`, and `matplotlib` install cleanly from `conda-forge`.

```bash
cd /path/to/proteomescout-v4
conda env create -f environment.yml
conda activate pscout
python run.py
```

Then open:

```text
http://127.0.0.1:5001/proteins
```

`run.py` defaults to port `5001`.
If needed, choose a different port with:

```bash
PORT=5050 python run.py
```

If your TSV files are not in the default location, run with:

```bash
PROTEOMESCOUT_DATA_DIR=/path/to/proteomescout_data \
python run.py
```

That directory should contain both `data.tsv` and `citations.tsv`.

## Optional: local `.venv` inside conda

Only do this if you specifically want a workspace-local interpreter path for VS Code.
It is not required for normal usage.

```bash
cd /path/to/proteomescout-v4
conda create -n pscout-base -c conda-forge python=3.11 pip
conda activate pscout-base
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install debugpy
python run.py
```

## VS Code

Use the `Python: ProteomeScout App` debug profile.

If you use conda only, select the `pscout` interpreter in VS Code.

If you use `.venv`, select:

```text
/path/to/proteomescout-v4/.venv/bin/python
```