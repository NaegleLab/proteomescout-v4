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

## Container Deployment

This repository ships a `Dockerfile`, `.dockerignore`, and `docker-compose.yml`.
Docker and Docker Compose are the only runtime dependencies — no Python or conda
installation needed on the host.

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine + Compose plugin on Linux)
- The ProteomeScout dataset directory (see **Data** below)

### Data

Download the Jan 2026 dataset from Figshare:
[https://doi.org/10.6084/m9.figshare.31129045.v1](https://doi.org/10.6084/m9.figshare.31129045.v1)

Extract the archive. The deployment expects a single directory (referred to below
as `ProteomeScout_Dataset`) that contains **directly**:

```
ProteomeScout_Dataset/
    data.tsv         # ~117 MB — full PTM dataset
    citations.tsv    # experiment / citation metadata
```

`citations.tsv` must include a `Current` column (values `TRUE` / `FALSE`) to
control which citations appear in the UI.

### Setup

```bash
# 1. Clone the repo
git clone https://github.com/<org>/proteomescout-v4.git
cd proteomescout-v4

# 2. Create your local environment file (never committed)
cp .env.example .env
```

Edit `.env` with the two required values:

```bash
# Absolute path to the directory that directly contains data.tsv and citations.tsv
PROTEOMESCOUT_DATA_HOST_DIR=/path/to/ProteomeScout_Dataset

# Flask secret key — generate one with:
#   python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=replace-with-a-strong-random-secret
```

### Run (Docker Compose)

```bash
# Build image and start container in the foreground (Ctrl-C to stop)
docker compose up --build

# Or run in the background
docker compose up --build -d
docker compose logs -f proteomescout   # follow logs
docker compose down                    # stop and remove container
```

The app is available at:

```
http://localhost:5001/
```

### Volume and Environment Variable Reference

| Variable | Where set | Purpose |
|---|---|---|
| `PROTEOMESCOUT_DATA_HOST_DIR` | `.env` | Host path mounted into the container |
| `SECRET_KEY` | `.env` | Flask session signing key |
| `PROTEOMESCOUT_DATA_DIR` | `docker-compose.yml` | Path inside container to TSV files |
| `PROTEOMESCOUT_API_DATA_DIR` | `docker-compose.yml` | Parent path for ProteomeScoutAPI |
| `PORT` | `docker-compose.yml` | Container port (default `5001`) |
| `DEBUG` | `docker-compose.yml` | Set to `false` in all non-development environments |

The compose file mounts `${PROTEOMESCOUT_DATA_HOST_DIR}` to
`/data_root/ProteomeScout_Dataset` inside the container, then sets:

- `PROTEOMESCOUT_DATA_DIR=/data_root/ProteomeScout_Dataset`
- `PROTEOMESCOUT_API_DATA_DIR=/data_root`

No symlinks or additional directory structure are required on the host.

## Cloud / HPC Deployment

The container image can be deployed on any OCI-compatible runtime
(AWS ECS/Fargate, Google Cloud Run, Azure Container Apps, Kubernetes, Singularity/Apptainer on HPC, etc.).

### 1. Build and push the image

```bash
docker build -t <registry>/<namespace>/proteomescout-v4:<tag> .
docker push <registry>/<namespace>/proteomescout-v4:<tag>
```

### 2. Mount data and set environment variables

Mount a persistent volume at `/data_root/ProteomeScout_Dataset` containing
`data.tsv` and `citations.tsv`, then set:

| Variable | Value |
|---|---|
| `HOST` | `0.0.0.0` |
| `PORT` | `5001` |
| `DEBUG` | `false` |
| `SECRET_KEY` | strong random secret (≥ 32 hex chars) |
| `PROTEOMESCOUT_DATA_DIR` | `/data_root/ProteomeScout_Dataset` |


### 3. Expose the service

- Container port: `5001`
- Health check path: `GET /`

### 4. Production notes

- Use a persistent volume backed by shared storage — do not bake data into the image.
- Keep `DEBUG=false`; it disables the Werkzeug debugger and pin-based reloader.
- Restrict inbound access as required by your institutional network policy.

