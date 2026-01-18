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

En produccion, el frontend se sirve como estatico desde el Nginx del host y la API/Mongo van en Docker.

1) Construir el frontend:
```
cd static
npm ci
npm run build
```

2) Copiar `static/dist` al directorio servido por Nginx (por ejemplo `/var/www/concurso`).

Notas:
- Nginx sirve el contenido de `static/dist` y hace proxy a la API en `/api`.
- Los contenedores de produccion se levantan con:
```
docker compose -f docker-compose.prod.yml up -d
```
- El servicio `api` expone `127.0.0.1:3000` y monta las fotos desde `/var/lib/concurso/fotos`.
- Para reindexar fotos en produccion:
```
docker compose -f docker-compose.prod.yml run --rm ingest
```
- Para subir fotos desde tu maquina local (ejemplo con tar):
```
tar -czf fotos.tar.gz /ruta/a/tus/fotos
scp fotos.tar.gz pablo@TU_SERVIDOR:/tmp/
```
- En el servidor, descomprimir y ajustar permisos:
```
sudo tar -xzf /tmp/fotos.tar.gz -C /var/lib/concurso/fotos --strip-components=1
sudo chmod -R o+rX /var/lib/concurso/fotos
```

## Deployment automatico (GitHub Actions + SSH)

Al hacer push a `main`, el workflow `deploy` se conecta por SSH y ejecuta el despliegue.
Debes configurar estos secrets en el repositorio:

- `DEPLOY_HOST`: host o IP del servidor.
- `DEPLOY_USER`: usuario SSH.
- `DEPLOY_SSH_KEY`: clave privada SSH.
- `DEPLOY_WEB_PATH`: ruta en el servidor donde se copian los archivos estaticos (`static/dist`).

Notas:
- El workflow usa `/opt/concurso` en el servidor para el repo y `docker-compose.prod.yml`.
- El repo debe estar clonado en `/opt/concurso` para que `git pull` funcione.
