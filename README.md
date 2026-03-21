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

This repository includes:

- `Dockerfile`
- `.dockerignore`
- `docker-compose.yml`

### Local Container Test (Docker Compose)

1. Prepare a host data directory that contains:
	 - `data.tsv`
	 - `citations.tsv`

2. (Recommended) Make the same files visible to ProteomeScoutAPI's expected path:

```bash
mkdir -p /absolute/path/to/proteomescout_data/ProteomeScout_Dataset
ln -sf ../data.tsv /absolute/path/to/proteomescout_data/ProteomeScout_Dataset/data.tsv
ln -sf ../citations.tsv /absolute/path/to/proteomescout_data/ProteomeScout_Dataset/citations.tsv
```

3. Start the app:

```bash
cd <dir_to_clone>/proteomescout-v4
export PROTEOMESCOUT_DATA_HOST_DIR=/absolute/path/to/proteomescout_data
docker compose up --build
```

4. Open:

```text
http://127.0.0.1:5001/
```

5. Stop:

```bash
docker compose down
```

### Local Container Test (Plain Docker)

```bash
cd <dir_to_clone>/proteomescout-v4
docker build -t proteomescout-v4:latest .

docker run --rm -p 5001:5001 \
	-e SECRET_KEY=change-me \
	-e HOST=0.0.0.0 \
	-e PORT=5001 \
	-e DEBUG=false \
	-e PROTEOMESCOUT_DATA_DIR=/data \
	-e PROTEOMESCOUT_API_DATA_DIR=/data \
	-v /absolute/path/to/proteomescout_data:/data:rw \
	proteomescout-v4:latest
```

## Cloud Deployment

This app is suitable for cloud container services such as AWS ECS/Fargate,
Google Cloud Run, Azure Container Apps, and Kubernetes.

### 1. Build and Push Image

```bash
docker build -t <registry>/<namespace>/proteomescout-v4:<tag> .
docker push <registry>/<namespace>/proteomescout-v4:<tag>
```

### 2. Runtime Settings

Set these container environment variables:

- `HOST=0.0.0.0`
- `PORT=5001`
- `DEBUG=false`
- `SECRET_KEY=<strong-random-secret>`
- `PROTEOMESCOUT_DATA_DIR=/data`
- `PROTEOMESCOUT_API_DATA_DIR=/data`

Mount persistent storage at `/data` containing:

- `/data/data.tsv`
- `/data/citations.tsv`

And, for ProteomeScoutAPI compatibility, also ensure:

- `/data/ProteomeScout_Dataset/data.tsv`
- `/data/ProteomeScout_Dataset/citations.tsv`

These can be symlinks to the top-level TSV files.

### 3. Expose Service

- Container port: `5001`
- Health check path: `/`

### 4. Production Notes

- Use a persistent volume (do not rely on ephemeral container storage).
- Run multiple replicas behind a load balancer if needed.
- Keep `DEBUG=false` in cloud environments.
- Restrict inbound access as required by your research environment.

