### Agenda de Citas - Cypherstudios

- Documentación Técnica y Arquitectura del Sistema (V2)
  Este documento detalla la arquitectura, el modelo de datos y la configuración de infraestructura para el sistema SaaS ligero de gestión de citas de Cypherstudios. El sistema está diseñado bajo un modelo híbrido: servicios perimetrales y de aplicación locales contenerizados, con persistencia administrada en la nube mediante Supabase (PostgreSQL).

1.  Arquitectura de Red e Infraestructura Docker
    El entorno se despliega utilizando Docker Compose en una solución de dos capas (Edge/Application) locales que consumen un servicio externo de base de datos.

                      [ Petición Externa / Internet ]
                                    │ (Puerto 9090 - HTTPS)
                                    ▼
             ┌──────────────────────────────────────────────┐
             │ CONTAINER: Nginx (Reverse Proxy & Static)    │
             │ - Termina SSL (Certificado Autofirmado/DDNS) │
             │ - Sirve archivos de /public directamente     │
             └──────────────────────┬───────────────────────┘
                                    │ (Red Interna Docker)
                                    ▼
             ┌──────────────────────────────────────────────┐
             │ CONTAINER: FastAPI Application Server        │
             │ - Puerto 8000 (Bloqueado al exterior)        │
             │ - Lógica de negocio y Autenticación JWT     │
             └──────────────────────┬───────────────────────┘
                                    │ (Internet seguro / TLS)
                                    ▼
             ┌──────────────────────────────────────────────┐
             │ EXTERNAL: Supabase (Cloud PostgreSQL)        │
             │ - Persistencia gestionada en la nube         │
             └──────────────────────────────────────────────┘

    Componentes de la Infraestructura

Nginx (Puerto 9090 → 80 interno): Único punto de entrada expuesto al host de Windows. Actúa como proxy inverso con TLS/SSL para proteger la aplicación y sirve el contenido estático de la interfaz (/public).

FastAPI / Uvicorn (Puerto 8000 interno): Bloqueado por completo al tráfico externo directo. Solo procesa solicitudes redirigidas por Nginx a través de la red interna de Docker.

Supabase (PostgreSQL en la nube): Aloja la persistencia de datos, eliminando la necesidad de gestionar almacenamiento local o contenedores pesados de bases de datos.

2. Configuración del Entorno y Orquestación
   Archivo .env (Raíz del Proyecto)
   Centraliza la configuración para facilitar la portabilidad entre desarrollo (localhost) y producción con tu dominio DDNS.

Bash

# Variables del Sistema y Red

APP_ENV=development
SERVER_HOST=localhost
SERVER_PORT=9090
DDNS_DOMAIN=tu-subdominio.ddns.net # Preparado para No-IP

# Seguridad y Token

JWT_SECRET_KEY=9a7bcf36d2e14a8f90c123456789abcdef0123456789abcdef0123456789abc
ACCESS_TOKEN_EXPIRE_MINUTES=480

# Conexión Externa a Supabase

SUPABASE_DB_URL=postgresql://postgres.tu_id_supabase:tu_password@aws-0-eu-central-1.pooler.supabase.com:6543/postgres?sslmode=require
Archivo docker-compose.yml
YAML
version: '3.8'

services:
nginx:
image: nginx:alpine
container_name: cypherstudios_proxy
ports: - "${SERVER_PORT}:443"
    volumes:
      - ./public:/usr/share/nginx/html:ro
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/certs:/etc/nginx/certs:ro
    environment:
      - DDNS_DOMAIN=${DDNS_DOMAIN}
depends_on: - web
networks: - cypher_network

web:
build: ./servidor
container_name: cypherstudios_api
expose: - "8000"
env_file: - .env
volumes: - ./servidor:/app
command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
networks: - cypher_network

networks:
cypher_network:
driver: bridge 3. Configuración del Servidor Web Nginx y SSL
Nginx se encarga de mitigar ataques, servir el frontend en milisegundos y gestionar el cifrado TLS. El archivo está preparado para responder tanto a localhost como a tu futuro dominio dinámico de No-IP.

Archivo nginx.conf
Nginx
worker_processes auto;

events {
worker_connections 1024;
}

http {
include /etc/nginx/mime.types;
default_type application/octet-stream;

    sendfile        on;
    keepalive_timeout  65;

    # Bloquear información del servidor por seguridad
    server_tokens off;

    server {
        listen 443 ssl;
        # Acepta peticiones locales o del dominio DDNS dinámico
        server_name localhost tu-subdominio.ddns.net;

        # Configuración de Certificados SSL (Generados con OpenSSL)
        ssl_certificate     /etc/nginx/certs/cypherstudios.crt;
        ssl_certificate_key /etc/nginx/certs/cypherstudios.key;

        ssl_protocols       TLSv1.2 TLSv1.3;
        ssl_ciphers         HIGH:!aNULL:!MD5;

        # Carpeta Raíz del Frontend
        root /usr/share/nginx/html;
        index login.html;

        # Servir el Frontend directamente
        location / {
            try_files $uri $uri/ /login.html;
        }

        # Redirección de la API hacia el contenedor de FastAPI
        location /api/ {
            proxy_pass http://web:8000/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }

}
Generación del certificado local en Windows (Git Bash o PowerShell):

Bash
mkdir nginx/certs
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout nginx/certs/cypherstudios.key -out nginx/certs/cypherstudios.crt -subj "/CN=localhost" 4. Diseño del Esquema de la Base de Datos (SQL / Supabase)
Dado que usamos PostgreSQL a través de Supabase, adaptamos los tipos de datos nativos para optimizar el rendimiento y aplicar las restricciones del negocio solicitadas.

```SQL
-- 1. Tabla de Usuarios (Administradores/Gestores de la Agenda)
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido_1 VARCHAR(100) NOT NULL,
    apellido_2 VARCHAR(100),
    dni VARCHAR(20) UNIQUE NOT NULL,
    telefono VARCHAR(20),
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(64) NOT NULL, -- Almacenará SHA-256
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Tabla de Servicios Ofrecidos
CREATE TABLE servicios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(150) UNIQUE NOT NULL,
    descripcion TEXT,
    precio NUMERIC(10, 2) NOT NULL,
    activo BOOLEAN DEFAULT TRUE
);

-- 3. Tabla de Eventos / Citas (PK basada en String de Tiempo YYMMDDHHM)
CREATE TABLE eventos (
    id VARCHAR(10) PRIMARY KEY, -- Formato compacto YYMMDDHHM
    nombre_cliente VARCHAR(150) NOT NULL,
    apellido_1_cliente VARCHAR(100) NOT NULL,
    apellido_2_cliente VARCHAR(100),
    dni_cliente VARCHAR(20) NOT NULL,
    email_cliente VARCHAR(150) NOT NULL,
    telefono_cliente VARCHAR(20) NOT NULL,
    fecha DATE NOT NULL,          -- Formato YYYY-MM-DD
    hora TIME NOT NULL,           -- Formato HH:MM
    anotaciones TEXT,
    id_servicio INT NOT NULL,
    id_usuario_gestor INT NOT NULL, -- Quién registró la cita
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_servicio FOREIGN KEY (id_servicio) REFERENCES servicios(id),
    CONSTRAINT fk_usuario_gestor FOREIGN KEY (id_usuario_gestor) REFERENCES usuarios(id)
);

-- 4. Tabla de Consultas (Formulario de contacto externo público)
CREATE TABLE consultas (
    id SERIAL PRIMARY KEY,
    nombre_usuario VARCHAR(150) NOT NULL,
    email_usuario VARCHAR(150) NOT NULL, -- No es único (múltiples consultas)
    tema_consulta VARCHAR(200) NOT NULL,
    mensaje TEXT NOT NULL,
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

5. Lógica de Negocio y Seguridad (Backend en FastAPI)
   Cifrado de Contraseñas y Control de Acceso
   Algoritmo: Uso estricto de SHA-256 para hashear las credenciales antes de insertarlas en Supabase.

Autenticación: Implementación de OAuth2 con tokens JWT (JSON Web Tokens). Al loguearse, el servidor entrega un token firmado criptográficamente que el cliente almacena temporalmente y envía en las cabeceras Authorization: Bearer <token> de las rutas protegidas.

Flujo de Registro Cerrado: El endpoint POST /auth/register no cuenta con interfaz pública en el login. Únicamente puede ser invocado por el usuario administrador inicial para dar de alta a nuevos empleados, garantizando el aislamiento del sistema.

Control de Concurrencia y Solapamientos
Al migrar a PostgreSQL (Supabase), implementamos un sistema para asegurar que no ocurran reservas duplicadas en llamadas paralelas. En la ruta crítica de creación de eventos, se realiza un bloqueo selectivo de filas mediante SQLModel / SQLAlchemy utilizando la instrucción de exclusión:

```Python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from database import get_db
from models import Evento

router = APIRouter()

@router.post("/eventos/", status_code=status.HTTP_201_CREATED)
def crear_cita(evento_data: Evento, db: Session = Depends(get_db)):
    # Ejecutamos un bloqueo pesimista sobre la franja horaria e ID únicos de la cita
    # Si otra consulta intenta leer el mismo ID de tiempo simultáneamente, se encola
    statement = select(Evento).where(Evento.id == evento_data.id).with_for_update()
    cita_existente = db.exec(statement).first()

    if cita_existente:
        raise HTTPException(
            status_code=400,
            detail="La franja horaria seleccionada ya se encuentra ocupada."
        )

    db.add(evento_data)
    db.commit()
    db.refresh(evento_data)
    return {"status": "success", "data": evento_data}
```

6. Estructura de Archivos del Proyecto
   Siguiendo un estándar profesional y desacoplado, organizamos el código de la siguiente manera:

```Bash
cypherstudios-project/
│
├── .env # Variables de entorno críticas
├── .gitignore # Exclusiones de Git
├── .dockerignore # Exclusiones de construcción de imágenes
├── docker-compose.yml # Orquestador de contenedores
│
├── nginx/ # Configuración del servidor perimetral
│ ├── nginx.conf
│ └── certs/
│ ├── cypherstudios.crt
│ └── cypherstudios.key
│
├── public/ # FRONTEND (Servido por Nginx)
│ ├── login.html # Vista de acceso inicial
│ ├── index.html # Calendario de gestión principal
│ ├── js/
│ │ ├── auth.js # Control de Tokens JWT y Login
│ │ └── app.js # Lógica dinámica del calendario
│ └── style/
│ └── index.css # Tailwind CSS compilado + Variables :root
│
└── servidor/ # BACKEND (Python FastAPI)
├── Dockerfile
├── requirements.txt # Dependencias (fastapi, uvicorn, sqlmodel, psycopg2-binary)
├── main.py # Inicializador de la aplicación
├── database.py # Configuración de sesión hacia Supabase
├── models.py # Declaración de clases SQLModel
└── routers/
├── auth.py # Endpoints de Login y gestión de usuarios (SHA-256)
├── eventos.py # Gestión de citas con bloqueo pesimista
└── servicios.py # Endpoint dinámico GET /servicios 7. Archivos de Control de Versiones
Archivo .gitignore
Plaintext
```

# Entorno Local

.env
nginx/certs/_.crt
nginx/certs/_.key

# Python

**pycache**/
_.py[cod]
_$py.class
.venv/
env/
venv/
.pytest_cache/

# IDEs

.idea/
.vscode/
_.suo
_.ntvs\*
_.njsproj
_.sln
Archivo .dockerignore
Plaintext
.git
.gitignore
.dockerignore
.idea
.vscode
servidor/.venv
servidor/env
README.md

8. Sincronización Dinámica de la Interfaz (JS)
   Con el nuevo modelo, las funciones clave del frontend mutan de usar localStorage a interactuar de forma segura mediante peticiones asíncronas (fetch) que transportan las credenciales:

Carga Inicial (GET /servicios): Al inicializar la vista del formulario, se realiza una petición al backend para renderizar el dropdown de servicios de forma dinámica con los precios reales de Supabase.

Validación del Estado Horario: La visualización de los bloques horario entre las 08:00 y 14:00 se dibuja enviando la fecha seleccionada al endpoint de la API. Las horas devuelvas que posean un ID del tipo YYMMDDHHM se renderizan inmediatamente con la clase estética .locked. Las horas sin ID asociado se muestran con la clase .available.

```

```
