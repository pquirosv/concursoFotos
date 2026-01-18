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

## Produccion (assets estaticos optimizados)

Para servir el frontend como archivos estaticos optimizados (Vite build) se puede usar el stack de produccion:

1) Construir y levantar servicios:
```
docker compose -f docker-compose.prod.yml up --build
```

2) Abrir la UI:
- `http://localhost:8080`

Notas:
- El frontend se compila con `npm run build` dentro de `Dockerfile.nginx`.
- Nginx sirve el contenido de `static/dist` y hace proxy a la API en `/api`.

## Deployment automatico (GitHub Actions + SSH)

Al hacer push a `main`, el workflow `production-build` se conecta por SSH y ejecuta el despliegue.
Debes configurar estos secrets en el repositorio:

- `DEPLOY_HOST`: host o IP del servidor.
- `DEPLOY_USER`: usuario SSH.
- `DEPLOY_SSH_KEY`: clave privada SSH.
- `DEPLOY_PORT`: puerto SSH (por defecto 22).
- `DEPLOY_PATH`: ruta en el servidor donde vive el repo.
