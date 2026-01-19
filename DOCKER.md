# Run With Docker

Prereqs: Docker and Docker Compose installed.

## Dev compose (nginx + API + frontend + Mongo)

1) Build and start everything:
```bash
docker compose up --build
```

2) URLs:
- UI: `http://localhost:8080` (proxied through Nginx)
- API: `http://localhost:8080/api`
- Mongo (host port): `mongodb://localhost:27017/concurso`

## Notes

- The API image is built from `server/Dockerfile` with context at repo root.
- Nginx proxies `/` to the Vite dev server and `/api` to the API container.
- The photo files are served from `/fotos/` via Nginx. In `docker-compose.yml` that path is mapped from `/home/pablo/Imágenes/concursoDev`. Adjust that host path for your machine.
- There are two API containers:
  - `api_prod` on port `3000` (used by Nginx)
  - `api_test` on port `3001`
- The dataset is chosen via `DATASET` and maps to:
  - `prod` -> `photos_prod`
  - `test` -> `photos_test`

## Insert a sample document

This inserts into the `photos_prod` collection in the `concurso` database:
```bash
docker compose exec mongo mongosh "mongodb://localhost:27017/concurso" --eval 'db.photos_prod.insertOne({name:"paris.jpg",year:2021})'
```

## Run ingest in a container

This reads photos from the mapped host folder and writes into Mongo:
```bash
docker compose run --rm ingest
```

## Production compose

For the production-like stack (API + Mongo + ingest), use:
```bash
docker compose -f docker-compose.prod.yml up --build
```
