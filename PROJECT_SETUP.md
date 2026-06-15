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
