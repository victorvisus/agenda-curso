# PROJECT_SETUP.md

## Objetivo del documento

Este archivo recoge, paso a paso, la construccion del proyecto **Agenda de Citas - Cypherstudios**.

La idea es que sirva como guia de aprendizaje y como memoria tecnica del proyecto: que se hizo, por que se hizo y como se comprobo que funcionaba.

---

## Paso 1 - Analisis inicial del proyecto

Antes de crear archivos de codigo o infraestructura, se revisaron los documentos existentes originalmente en la raiz del proyecto:

- `README.md`
- `DOCUMENTACION.md`
- `ESPECIFICACIONES_TECNICAS.md`
- `CONOCIMIENTOS_DOCKER.md`
- `CONOCIMIENTOS_GIT.md`
- `CONOCIMIENTOS_JAVASCRIPT.md`
- `CONOCIMIENTOS_PYTHON.md`

Posteriormente, estos archivos fueron movidos a la carpeta `docs/` para mantener la raiz del proyecto mas limpia.

### Conclusiones principales

El proyecto sera una agenda de citas/servicios para Cypherstudios.

La arquitectura objetivo documentada es:

- **Nginx** como punto de entrada unico.
- **FastAPI** como backend interno.
- **Supabase/PostgreSQL** como base de datos externa gestionada.
- **Docker Compose** como herramienta para levantar el entorno de desarrollo.
- Frontend estatico servido desde la carpeta `public/`.

### Decision didactica

Aunque la documentacion final plantea HTTPS desde el principio, se decidio empezar con HTTP local para validar primero la comunicacion basica:

```text
Navegador -> Nginx -> FastAPI
```

Una vez validada esa base, se podra anadir HTTPS como una capa posterior.

---

## Paso 2 - Creacion de la estructura base de carpetas

Se creo la estructura inicial del proyecto:

```text
calendario-curso/
├── nginx/
│   └── certs/
├── public/
│   ├── js/
│   └── style/
└── servidor/
    └── routers/
```

### Para que sirve cada carpeta

- `nginx/`: configuracion del servidor Nginx.
- `nginx/certs/`: certificados locales cuando se active HTTPS.
- `public/`: archivos estaticos del frontend.
- `public/js/`: JavaScript del frontend.
- `public/style/`: CSS del frontend.
- `servidor/`: backend Python con FastAPI.
- `servidor/routers/`: rutas modulares de la API.

---

## Paso 3 - Archivos de control del proyecto

Se crearon los siguientes archivos en la raiz:

```text
.gitignore
.dockerignore
.env.example
.env
```

### `.gitignore`

Sirve para evitar que Git suba archivos sensibles o innecesarios.

Incluye exclusiones para:

- `.env`
- certificados locales
- entornos virtuales de Python
- cache de Python
- carpetas de datos locales
- configuraciones de IDE

### `.dockerignore`

Sirve para evitar que Docker copie al contexto de construccion archivos que no necesita.

Esto ayuda a:

- construir imagenes mas limpias,
- evitar copiar documentacion innecesaria,
- no incluir entornos virtuales dentro de la imagen.

### `.env.example`

Plantilla publica de variables de entorno.

No contiene secretos reales. Sirve para documentar que variables necesita el proyecto.

### `.env`

Archivo real de configuracion local.

> Importante: este archivo esta ignorado por Git y no debe subirse al repositorio.

Variables iniciales:

```bash
APP_ENV=development
SERVER_HOST=localhost
SERVER_PORT=9090
DDNS_DOMAIN=tu-subdominio.ddns.net

JWT_SECRET_KEY=cambia-este-valor-por-uno-largo-y-secreto
ACCESS_TOKEN_EXPIRE_MINUTES=480

SUPABASE_DB_URL=postgresql://postgres.tu_id_supabase:tu_password@aws-0-eu-central-1.pooler.supabase.com:6543/postgres?sslmode=require
```

---

## Paso 4 - Docker Compose inicial

Se creo el archivo:

```text
docker-compose.yml
```

Este archivo levanta dos servicios:

### Servicio `nginx`

Usa la imagen:

```text
nginx:1.25-alpine
```

Responsabilidades:

- exponer el puerto `9090` en Windows,
- servir el frontend desde `public/`,
- redirigir las rutas `/api/` hacia FastAPI.

Mapeo actual:

```text
localhost:9090 -> contenedor nginx:80
```

### Servicio `web`

Construye una imagen propia desde:

```text
servidor/Dockerfile
```

Responsabilidades:

- ejecutar FastAPI con Uvicorn,
- escuchar internamente en el puerto `8000`,
- no exponer ese puerto directamente al sistema host.

Comando de desarrollo:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Red interna

Se creo una red Docker:

```text
cypher_network
```

Nginx y FastAPI se comunican a traves de esta red interna.

---

## Paso 5 - Configuracion minima de Nginx

Se creo:

```text
nginx/nginx.conf
```

Configuracion actual:

- Nginx escucha en el puerto interno `80`.
- Sirve los archivos de `public/`.
- Usa `login.html` como pagina inicial.
- Redirige `/api/` al contenedor `web` en el puerto `8000`.

Fragmento importante:

```nginx
location /api/ {
    proxy_pass http://web:8000/;
}
```

Esto significa:

```text
http://localhost:9090/api/health
```

termina llamando internamente a:

```text
http://web:8000/health
```

---

## Paso 6 - Backend minimo con FastAPI

Se crearon los archivos:

```text
servidor/Dockerfile
servidor/requirements.txt
servidor/main.py
```

### `servidor/Dockerfile`

Define como construir la imagen del backend.

Base utilizada:

```dockerfile
FROM python:3.12-slim
```

### `servidor/requirements.txt`

Dependencias iniciales:

```text
fastapi
uvicorn[standard]
sqlmodel
psycopg2-binary
python-jose[cryptography]
```

### `servidor/main.py`

Se creo una aplicacion minima:

```python
from fastapi import FastAPI

app = FastAPI(title="Agenda de Citas - Cypherstudios")


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "agenda-api"}
```

La ruta `/health` sirve para comprobar que la API esta viva.

---

## Paso 7 - Frontend minimo

Se crearon:

```text
public/login.html
public/style/index.css
```

La pagina inicial muestra:

- nombre del proyecto,
- mensaje de infraestructura inicial,
- enlace a `/api/health`.

Por ahora el frontend no tiene logica de negocio. Solo sirve para comprobar que Nginx esta sirviendo archivos estaticos correctamente.

---

## Paso 8 - Levantar el entorno

Se ejecuto:

```bash
docker compose up -d --build
```

Este comando:

- descarga la imagen de Nginx si no existe,
- construye la imagen del backend,
- crea la red interna,
- arranca los contenedores.

### Contenedores levantados

```text
cypherstudios_api
cypherstudios_proxy
```

Estado comprobado:

```text
cypherstudios_api     Up   8000/tcp
cypherstudios_proxy   Up   0.0.0.0:9090->80/tcp
```

---

## Paso 9 - Verificacion de funcionamiento

Se probaron dos rutas desde Windows:

### Frontend

```text
http://localhost:9090
```

Resultado:

```text
HTTP 200
```

Esto confirma que Nginx esta sirviendo el frontend.

### API a traves de Nginx

```text
http://localhost:9090/api/health
```

Resultado:

```json
{"status":"ok","service":"agenda-api"}
```

Esto confirma que:

```text
Windows -> Nginx -> FastAPI
```

funciona correctamente.

---

## Estado actual

La infraestructura minima de desarrollo esta funcionando.

Tenemos validado:

- Docker Compose.
- Nginx como punto de entrada.
- FastAPI como backend interno.
- Red interna entre contenedores.
- Frontend estatico servido por Nginx.
- Proxy inverso desde `/api/` hacia FastAPI.

### Organizacion actual de documentacion

Los documentos de analisis y conocimientos del curso se movieron a:

```text
docs/
```

Se mantiene `PROJECT_SETUP.md` en la raiz porque es el registro vivo de construccion del proyecto.

Tambien se actualizo `.dockerignore` para excluir:

```text
docs/
PROJECT_SETUP.md
```

Asi evitamos copiar documentacion dentro del contexto de construccion de Docker.

---

## Proximo paso recomendado

Preparar Git correctamente:

1. Inicializar el repositorio.
2. Comprobar que `.env` queda ignorado.
3. Revisar los archivos que entraran en el primer commit.
4. Crear el primer commit limpio de infraestructura.

---

## Paso 10 - Inicializacion del repositorio Git local

Se inicializo el repositorio Git en la raiz del proyecto:

```bash
git init -b main
```

Esto creo la carpeta interna `.git/` y dejo la rama principal con el nombre `main`.

### Comprobacion de archivos ignorados

Antes de hacer el primer commit, se verifico que los archivos sensibles quedaban fuera del repositorio:

```bash
git check-ignore -v .env nginx/certs/cypherstudios.crt nginx/certs/cypherstudios.key
```

Resultado esperado:

- `.env` queda ignorado por `.gitignore`.
- `nginx/certs/*.crt` queda ignorado.
- `nginx/certs/*.key` queda ignorado.

Esto es importante porque el repositorio no debe contener secretos, credenciales ni claves privadas.

### Preparacion del primer commit

Se anadieron los archivos al area de staging:

```bash
git add .
```

Despues se reviso el estado:

```bash
git status --short
```

Se comprobo que entraban los archivos de infraestructura, codigo minimo y documentacion, pero no `.env` ni certificados.

### Primer commit

Se creo el primer commit:

```bash
git commit -m "Initial project infrastructure"
```

Commit generado:

```text
316248d Initial project infrastructure
```

Este commit contiene la infraestructura inicial del proyecto:

- Docker Compose.
- Nginx.
- FastAPI minimo.
- Frontend minimo.
- Documentacion en `docs/`.
- Registro vivo `PROJECT_SETUP.md`.

### Estado de GitHub CLI

Se comprobo si estaba instalada la herramienta oficial de GitHub:

```bash
gh --version
```

Resultado:

```text
gh no esta instalado o no esta disponible en el PATH
```

Por tanto, la conexion con GitHub se hara mediante URL remota del repositorio creado en GitHub.

---

## Proximo paso recomendado

Crear un repositorio vacio en GitHub y copiar su URL remota.

Despues se ejecutara:

```bash
git remote add origin <URL_DEL_REPOSITORIO>
git push -u origin main
```

---

## Paso 11 - Conexion con GitHub

Se creo/configuro el repositorio remoto en GitHub:

```text
https://github.com/victorvisus/agenda-curso.git
```

### Anadir remoto `origin`

Se conecto el repositorio local con GitHub:

```bash
git remote add origin https://github.com/victorvisus/agenda-curso.git
```

Despues se verifico:

```bash
git remote -v
```

Resultado:

```text
origin  https://github.com/victorvisus/agenda-curso.git (fetch)
origin  https://github.com/victorvisus/agenda-curso.git (push)
```

### Subida inicial

Se subio la rama principal:

```bash
git push -u origin main
```

Resultado:

```text
branch 'main' set up to track 'origin/main'
main -> main
```

Esto significa que la rama local `main` queda vinculada con la rama remota `origin/main`.

A partir de ahora, para subir cambios despues de hacer commits, normalmente bastara con:

```bash
git push
```

---

## Estado Git actual

Repositorio local:

```text
C:\AppDesarrollo\CursoProyectos\calendario-curso
```

Repositorio remoto:

```text
https://github.com/victorvisus/agenda-curso.git
```

Rama principal:

```text
main
```

---

## Nota pendiente - Concurrencia y lecturas sucias en base de datos

Se anadio un nuevo documento de referencia:

```text
docs/LECTURA_SUCIA_BBDD.md
```

Este archivo se tendra en cuenta cuando se implemente la capa de base de datos y las rutas que modifican informacion critica.

### Ideas importantes a recordar

- Las lecturas sucias no se resuelven desde Docker, sino desde la base de datos.
- Hay que revisar el nivel de aislamiento de las transacciones.
- Para operaciones criticas conviene usar bloqueo pesimista con `FOR UPDATE`.
- En SQLModel/SQLAlchemy esto se expresa con:

```python
statement = select(Modelo).where(Modelo.id == modelo_id).with_for_update()
```

- La aplicacion no debe conectarse a la base de datos con un usuario administrador o `root`.
- El usuario de base de datos de la app debe tener permisos limitados.

### Decision para mas adelante

Cuando construyamos `servidor/database.py` y las rutas de escritura, especialmente creacion, actualizacion o cancelacion de citas, se revisara:

1. Nivel de aislamiento de la conexion.
2. Uso de `with_for_update()` en operaciones sensibles.
3. Restricciones unicas en base de datos para evitar duplicados.
4. Permisos minimos del usuario de conexion.

Esta nota queda marcada como importante para la fase de persistencia.

---

## Paso 12 - HTTPS local con certificados de confianza (mkcert)

### Problema detectado

El proyecto ya tenia configurado Nginx con HTTPS (puerto 443 con SSL), pero los certificados eran autofirmados con OpenSSL.

Esto provocaba que el navegador mostrara el aviso:

```text
Tu conexion no es privada
```

Para desarrollo local esto es molesto y puede enmascarar otros problemas de red.

### Solucion: mkcert

Se utilizo la herramienta `mkcert` para generar certificados de desarrollo que el sistema operativo y el navegador reconocen como de confianza.

`mkcert` funciona creando una Autoridad Certificadora (CA) local propia e instalandola en el almacen de confianza del sistema. Los certificados que genera estan firmados por esa CA, por lo que el navegador los acepta sin avisos.

### Instalacion de la CA local

Se verifico que mkcert estaba instalado:

```bash
mkcert --version
```

Resultado:

```text
v1.4.4
```

Se confirmo que la CA local ya estaba creada:

```bash
mkcert -install
```

Resultado:

```text
The local CA is already installed in the system trust store!
```

### Generacion de certificados

Se generaron los certificados reemplazando los anteriores autofirmados:

```bash
mkcert -key-file nginx/certs/cypherstudios.key -cert-file nginx/certs/cypherstudios.crt localhost 127.0.0.1 ::1
```

Resultado:

```text
Created a new certificate valid for the following names:
 - "localhost"
 - "127.0.0.1"
 - "::1"

It will expire on 16 September 2028
```

Los certificados cubren `localhost`, la IP `127.0.0.1` y la direccion IPv6 `::1`.

### Instalacion de la CA en el almacen del sistema

Despues de generar los certificados, Chrome seguia mostrando el aviso de conexion no segura.

Se descubrio que la CA de mkcert estaba instalada en el almacen de certificados del **usuario**, pero Chrome en Windows usa el almacen del **sistema**.

Se verifico:

```bash
certutil -user -store Root | findstr /i mkcert
```

Resultado: la CA aparecia aqui.

```bash
certutil -store Root | findstr /i mkcert
```

Resultado: la CA no aparecia.

Se instalo en el almacen del sistema con permisos de administrador:

```powershell
Start-Process certutil -ArgumentList '-addstore','Root','C:\Users\Victor\AppData\Local\mkcert\rootCA.pem' -Verb RunAs -Wait
```

Despues de esto, se verifico que la CA aparecia en ambos almacenes.

> Importante: despues de instalar la CA en el almacen del sistema, es necesario cerrar y reabrir Chrome completamente para que recargue los certificados.

### Redireccion HTTP a HTTPS

Se modifico la configuracion de Nginx para anadir un bloque `server` que escucha en el puerto 80 y redirige todo el trafico a HTTPS:

```nginx
server {
    listen 80;
    server_name localhost tu-subdominio.ddns.net;

    return 301 https://$host$request_uri;
}
```

Esto significa que cualquier peticion HTTP se convierte automaticamente en HTTPS con una redireccion permanente (301).

### Cambios en Docker Compose

Se anadio un segundo mapeo de puertos en el servicio `nginx`:

```yaml
ports:
  - "${SERVER_PORT_HTTP}:80"
  - "${SERVER_PORT}:443"
```

Esto expone ambos puertos al sistema host.

### Nueva variable de entorno

Se anadio la variable `SERVER_PORT_HTTP` en `.env` y `.env.example`:

```bash
SERVER_PORT_HTTP=9080
```

### Puertos locales resultantes

```text
localhost:9090  ->  contenedor nginx:443  (HTTPS)
localhost:9080  ->  contenedor nginx:80   (HTTP -> redirige a HTTPS)
```

### Verificacion

Se levantaron los contenedores:

```bash
docker compose down
docker compose up -d
```

Se comprobo el estado:

```bash
docker compose ps
```

Resultado:

```text
cypherstudios_api     Up   8000/tcp
cypherstudios_proxy   Up   0.0.0.0:9080->80/tcp, 0.0.0.0:9090->443/tcp
```

Se verificaron tres rutas:

1. HTTPS directo:

```text
https://localhost:9090/
```

Resultado: HTTP 200, pagina servida correctamente.

2. API a traves de HTTPS:

```text
https://localhost:9090/api/health
```

Resultado:

```json
{"status":"ok","service":"agenda-api"}
```

3. Redireccion HTTP a HTTPS:

```text
http://localhost:9080/
```

Resultado: HTTP 301, redireccion a `https://localhost/`.

El navegador ya no muestra el aviso de conexion no segura al acceder por HTTPS.

### Nota para cuando se configure el dominio externo

Cuando se obtenga el dominio en No-IP, habra que:

1. Regenerar los certificados con `mkcert` incluyendo el nuevo dominio.
2. Actualizar `server_name` en `nginx/nginx.conf`.
3. Para produccion real, sustituir mkcert por certificados de Let's Encrypt (Certbot).

---

## Estado actual

La infraestructura de desarrollo esta funcionando con HTTPS de confianza local.

Tenemos validado:

- Docker Compose con dos servicios.
- Nginx como punto de entrada con SSL/TLS.
- Certificados locales de confianza generados con mkcert.
- CA de mkcert instalada en el almacen del sistema (Chrome confía en ella).
- Redireccion automatica de HTTP a HTTPS.
- FastAPI como backend interno accesible a traves del proxy inverso.
- Frontend estatico servido por Nginx.
- Repositorio Git conectado a GitHub.

---

## Proximo paso recomendado - Dominio DDNS

Queda pendiente la configuracion del dominio dinamico (DDNS) a traves de No-IP.

Cuando se obtenga el subdominio, habra que:

1. Actualizar la variable `DDNS_DOMAIN` en `.env` con el dominio real.
2. Regenerar los certificados con `mkcert` incluyendo el nuevo dominio:

```bash
mkcert -key-file nginx/certs/cypherstudios.key -cert-file nginx/certs/cypherstudios.crt localhost 127.0.0.1 ::1 tu-dominio-real.ddns.net
```

3. Actualizar `server_name` en `nginx/nginx.conf` para que incluya el dominio real en lugar de `tu-subdominio.ddns.net`.
4. Reiniciar los contenedores para que Nginx cargue los nuevos certificados:

```bash
docker compose down
docker compose up -d
```

> Importante: los certificados de mkcert solo sirven para desarrollo local. Cuando el proyecto se exponga a internet, habra que sustituirlos por certificados reales de Let's Encrypt (Certbot) que el navegador de cualquier visitante pueda validar.

---

## ANEXO - Estado del entorno de desarrollo (16 de junio de 2026)

### Completado

- Estructura de carpetas del proyecto.
- Archivos de control: `.gitignore`, `.dockerignore`, `.env.example`, `.env`.
- Docker Compose con dos servicios (`nginx` y `web`).
- Nginx configurado como proxy inverso con SSL/TLS.
- Certificados locales de confianza generados con mkcert.
- CA de mkcert instalada en el almacen del sistema (Chrome no muestra avisos).
- Redireccion automatica de HTTP a HTTPS.
- FastAPI minimo con endpoint `/health`.
- Frontend estatico servido por Nginx.
- Repositorio Git inicializado y conectado a GitHub.

### Pendiente para poder trabajar (bloquea el desarrollo)

1. **Dar de alta la cuenta en Supabase** y crear el proyecto de base de datos PostgreSQL.
2. **Actualizar `SUPABASE_DB_URL` en `.env`** con la URL de conexion real (host, usuario, contrasena).
3. **Cambiar `JWT_SECRET_KEY` en `.env`** por un valor largo y seguro antes de implementar la autenticacion.

### Pendiente no bloqueante (se puede hacer mas adelante)

1. **Obtener el dominio DDNS en No-IP** y configurar el acceso externo.
2. **Regenerar los certificados con mkcert** incluyendo el nuevo dominio.
3. **Actualizar `server_name` en `nginx/nginx.conf`** con el dominio real.
4. **Sustituir mkcert por Let's Encrypt** cuando se exponga a internet.
