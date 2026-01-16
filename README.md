# Concurso de Fotos

Proyecto para mostrar fotos y jugar a adivinar el año a partir de una imagen. Incluye API (Node/Express + MongoDB), frontend (Vite) y un script de ingesta de fotos.

## Estructura

- `server/`: API y modelos.
- `static/`: frontend.
- `tools/photo_ingest/`: script de ingesta en Python.

## Ejecucion con Docker

1) Levantar servicios principales:
```
docker compose up --build
```

2) Abrir la UI:
- `http://localhost:8080` (via Nginx)

3) Ejecutar ingesta (one-shot):
```
docker compose run --rm ingest
```

## Notas

- Mongo se expone en `localhost:27017`.
- La API queda en `http://localhost:8080/api`.
- Las fotos se montan desde `/home/pablo/Imágenes/concursoDev` en el contenedor Nginx.
