# Run With Docker

Prereqs: Docker and Docker Compose installed.

## First time (after clone)

1) Create your local env file

2) Edit `.env` with **absolute host paths**:
```bash
PHOTOS_DIR=/path/to/your/photos
PHOTOS_OUT_DIR=/path/to/your/photos_out
```

3) Create the folders and put your photos in `PHOTOS_DIR`:
```bash
mkdir -p /path/to/your/photos /path/to/your/photos_out
```

4) Build and start everything:
```bash
docker compose up -d --build
```

5) Run ingestion (one-shot):
```bash
docker compose run --rm ingest
```
Note: inside the container the script always reads `/photos` and writes `/photos_out`.
Those map to your host paths defined in `.env` (`PHOTOS_DIR`, `PHOTOS_OUT_DIR`).

6) Open the UI:
- `http://localhost:8080` (proxied through Nginx)
- `http://localhost:5173` (Vite dev server)

## Notes

- Docker Compose reads variables from `.env`. If it is missing, defaults are used (`/var/lib/concurso/fotos` and `/var/lib/concurso/fotos_out`). If those paths are not writable on your host, set custom paths in `.env`.
- Nginx serves photos from `PHOTOS_OUT_DIR` at `/fotos/`.
- Ingest reads from `PHOTOS_DIR` and writes to `PHOTOS_OUT_DIR` (source is read-only).
- The API runs on port `3000` inside Docker and is proxied by Nginx at `/api`.
- The photos collection defaults to `photos` and can be overridden with `PHOTOS_COLLECTION`.

## Insert a sample document (optional)

This inserts into the `photos` collection in the `concurso` database:
```bash
docker compose exec mongo mongosh "mongodb://localhost:27017/concurso" --eval 'db.photos.insertOne({name:"paris.jpg",year:2021})'
```

## Production compose

For the production-like stack (API + Mongo + ingest), use:
```bash
docker compose -f docker-compose.prod.yml up --build
```

If you use the `ingest` service in production, ensure the compose file mounts both input and output folders (and that they exist on the host).
