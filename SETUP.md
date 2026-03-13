# App Setup

This setup is for the read-only TSV-backed app in `run.py`.
It is the primary runtime for this repository.

## Python Version

Use Python 3.11.x for development and production deployment.
Prefer patch-level updates within 3.11 and validate before moving to a newer minor version.

## Recommended: conda only

This is the simplest option on macOS ARM because `numpy`, `scipy`, and `matplotlib` install cleanly from `conda-forge`.

```bash
cd /Users/kmn4mj/GIT/public/proteomescout-v4
conda env create -f environment.yml
conda activate pscout
python run.py
```

Then open:

```text
http://127.0.0.1:5000/proteins
```

If your TSV files are not in the default location, run with:

```bash
PROTEIN_DATA_TSV_PATH=/Users/kmn4mj/GIT/Data/proteomescout_20260115/data.tsv \
CITATIONS_TSV_PATH=/Users/kmn4mj/GIT/Data/proteomescout_20260115/citations.tsv \
python run.py
```

## Optional: local `.venv` inside conda

Only do this if you specifically want a workspace-local interpreter path for VS Code.
It is not required for normal usage.

```bash
cd /Users/kmn4mj/GIT/public/proteomescout-v4
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
/Users/kmn4mj/GIT/public/proteomescout-v4/.venv/bin/python
```