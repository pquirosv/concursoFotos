# Photo Contest

Project to display photos and play a guessing game by year. It includes an API (Node/Express + MongoDB), a frontend (Vite), and a photo ingestion script.

## Quickstart (Docker)

1) Create `.env` with your local photo folders:

Edit `.env` and set **absolute paths**:
```
SOURCE_DIR=/path/to/your/photos
PHOTOS_DIR=/path/to/your/photos_out
```

2) Create the folders and put photos in `SOURCE_DIR`:
```bash
mkdir -p /path/to/your/photos /path/to/your/photos_out
```

3) Start the stack:
```bash
docker compose up -d --build
```

4) Run ingestion (one-shot):
```bash
docker compose run --rm ingest
```
Note: inside the container the script reads `/photos` and writes `/photos_out`.
Those map to your host paths defined in `.env` (`SOURCE_DIR`, `PHOTOS_DIR`).

5) Open the UI:
- `http://localhost:8080` (via Nginx)
- `http://localhost:5173` (Vite dev server)

## Structure

- `server/`: API and models.
- `static/`: frontend.
- `tools/photo_ingest/`: Python ingestion script.

The ingest service scans `SOURCE_DIR` recursively for supported image files, copies them into `PHOTOS_DIR`, extracts metadata (year from a `YYYYMMDD` filename pattern and optional city from a top-level folder), and writes records to MongoDB (default collection `photos`). It can optionally drop the collection before ingest (prompted).

## Run with Docker

1) Start core services:
```
docker compose up --build
```

2) Open the UI:
- `http://localhost:8080` (via Nginx)

3) Run ingestion (one-shot):
```
docker compose run --rm ingest
```
Note: inside the container the script reads `/photos` and writes `/photos_out`.
Those map to your host paths defined in `.env` (`SOURCE_DIR`, `PHOTOS_DIR`).

## Run frontend only (Vite dev server)

If you only want the frontend without Nginx, run Vite directly:
```
cd static
npm ci
npm run dev
```

Open `http://localhost:5173`.

## Sample photos for verification

There is a small set of photos under `static/public/fotos` that you can use to verify the UI is working.

## Notes

- Mongo is exposed at `localhost:27017`.
- The API is available at `http://localhost:8080/api`.
- Photos are served from `PHOTOS_DIR` under `/fotos/` by Nginx.

## Production (optimized static assets)

In production, the frontend is served statically by the host Nginx and the API/Mongo run in Docker.

1) Build the frontend:
```
cd static
npm ci
npm run build
```

2) Copy `static/dist` to the directory served by Nginx (for example `/var/www/concurso`).

Notes:
- Nginx serves `static/dist` and proxies the API under `/api`.
- Production containers are started with:
```
docker compose -f docker-compose.prod.yml up -d
```
- The `api` service exposes `127.0.0.1:3000`.
- To reindex photos in production:
```
docker compose -f docker-compose.prod.yml run --rm ingest
```
- To upload photos from your local machine (tar example):
```
tar -czf fotos.tar.gz /path/to/your/photos
scp fotos.tar.gz pablo@YOUR_SERVER:/tmp/
```
- On the server, extract and adjust permissions:
```
sudo tar -xzf /tmp/fotos.tar.gz -C /var/lib/concurso/fotos --strip-components=1
sudo chmod -R o+rX /var/lib/concurso/fotos
```
