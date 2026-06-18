# DOCUMENTO DE ESPECIFICACIONES TÉCNICAS Y ORDEN DE TRABAJO

**Para:** Equipo de Desarrollo Backend / Frontend / DevOps  
**Proyecto:** SaaS de Agenda de Citas Sincrónica – Cypherstudios  
**Estado:** Listo para Desarrollo (`Ready for Dev`)  
**Autor:** Analista Programador Senior

---

## 1. Stack Tecnológico Común y Flujo de Red

El sistema se compone de una arquitectura desacoplada basada en microservicios contenerizados locales y persistencia gestionada en la nube para optimizar recursos y garantizar portabilidad inmediata.

- **Capa Perimetral (Edge / Web Server):** Nginx (Contenedor local Alpine) configurado como Proxy Inverso, terminación de TLS/SSL y servidor de recursos estáticos de alto rendimiento.
- **Capa de Aplicación (Backend):** Python + FastAPI ejecutándose sobre el servidor ASGI Uvicorn (Contenedor local Linux-Slim).
- **Capa de Persistencia (Base de Datos):** PostgreSQL administrado y securizado en la nube a través de la plataforma **Supabase**.

### Aislamiento Estricto de Red (Docker Bridge)

El contenedor de la aplicación backend (`web`) estará completamente bloqueado al exterior y **no expondrá ningún puerto hacia el sistema operativo host (Windows)**. Toda la comunicación entrante se canaliza obligatoriamente a través del puerto expuesto `9090` del contenedor de Nginx.

Nginx resolverá las peticiones de la API a través de la red interna privada de Docker (`cypher_network`) apuntando al puerto interno `8000` de FastAPI.

---

## 2. Entorno, Orquestación y DevOps

El entorno de desarrollo se levantará de forma unificada mediante Docker Compose. El archivo orquestador leerá dinámicamente las credenciales y variables de entorno del archivo `.env` ubicado en la raíz del proyecto para asegurar la escalabilidad hacia dominios dinámicos (DDNS como No-IP).

### 2.1. Variables de Entorno (`.env`)

File written successfully.

```bash
# Variables de Sistema y Red Local
APP_ENV=development
SERVER_HOST=localhost
SERVER_PORT=9090
DDNS_DOMAIN=tu-subdominio.ddns.net  # Preparado para mapeo dinámico No-IP

# Seguridad y Criptografía
JWT_SECRET_KEY=9a7bcf36d2e14a8f90c123456789abcdef0123456789abcdef0123456789abc
ACCESS_TOKEN_EXPIRE_MINUTES=480

# String de Conexión de Pooling a Supabase (PostgreSQL TLS)
SUPABASE_DB_URL=postgresql://postgres.tu_id_supabase:tu_password@aws-0-eu-central-1.pooler.supabase.com:6543/postgres?sslmode=require`
```

### 2.2. Archivo de Orquestación (docker-compose.yml)

```YAML
services:
  nginx:
    image: nginx:1.25-alpine
    container_name: cypherstudios_proxy
    ports:
      - "${SERVER_PORT}:443"
    volumes:
      - ./public:/usr/share/nginx/html:ro
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/certs:/etc/nginx/certs:ro
    environment:
      - DDNS_DOMAIN=${DDNS_DOMAIN}
    depends_on:
      - web
    networks:
      - cypher_network

  web:
    build:
      context: ./servidor
      dockerfile: Dockerfile
    container_name: cypherstudios_api
    expose:
      - "8000"
    env_file:
      - .env
    volumes:
      - ./servidor:/app
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    networks:
      - cypher_network

networks:
  cypher_network:
    driver: bridge
```

### 2.3. Configuración Perimetral (nginx/nginx.conf)

El proxy inverso mitiga el escaneo de software ocultando metadatos sensibles (server_tokens off), levanta las políticas de TLS local y unifica el punto de entrada para evitar problemas cross-origin.

```Nginx
worker_processes auto;

events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    sendfile        on;
    server_tokens   off;

    server {
        listen 443 ssl;
        # Escucha tanto localmente como en el futuro dominio dinámico DDNS
        server_name localhost tu-subdominio.ddns.net;

        # Directivas de seguridad criptográfica SSL/TLS
        ssl_certificate     /etc/nginx/certs/cypherstudios.crt;
        ssl_certificate_key /etc/nginx/certs/cypherstudios.key;
        ssl_protocols       TLSv1.2 TLSv1.3;
        ssl_ciphers         HIGH:!aNULL:!MD5;

        # Raíz del Frontend (Single Page/Static Delivery)
        root /usr/share/nginx/html;
        index login.html;

        # Rutas de Interfaz de Usuario
        location / {
            try_files $uri $uri/ /login.html;
        }

        # Redirección interna hacia el contenedor FastAPI
        location /api/ {
            proxy_pass http://web:8000/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

### 3. Capa de Datos y Esquema Relacional (Supabase / PostgreSQL)

El backend utilizará un ORM asíncrono o síncrono (SQLModel o SQLAlchemy con el driver psycopg2-binary).

Regla de Negocio Crítica: La clave primaria (PK) de la tabla eventos no es un entero secuencial autoincremental. Se utilizará el string compacto generado por la lógica de negocio (YYMMDDHHM), optimizando las búsquedas directas por clave única.

```sql
-- DDL de Estructuras Relacionales para Supabase

-- 1. Tabla de Usuarios (Personal de gestión de Cypherstudios)
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido_1 VARCHAR(100) NOT NULL,
    apellido_2 VARCHAR(100),
    dni VARCHAR(20) UNIQUE NOT NULL,
    telefono VARCHAR(20),
    email VARCHAR(150) UNIQUE NOT NULL,
    pwd VARCHAR(64) NOT NULL, -- Almacenará SHA-256
    creado TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
-- 1.2. Tabla Cliente (Clientes a quienes se les ofrece el servicio)
CREATE TABLE clientes (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    apellido_1 VARCHAR(100) NOT NULL,
    apellido_2 VARCHAR(100),
    dni VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    telefono VARCHAR(20) NOT NULL,
);

-- 2. Tabla de Catálogo de Servicios
CREATE TABLE servicios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(150) UNIQUE NOT NULL,
    descripcion TEXT,
    precio NUMERIC(10, 2) NOT NULL,
    activo BOOLEAN DEFAULT TRUE
);

-- 3. Tabla Core de la Agenda (Eventos / Citas)
CREATE TABLE eventos (
    id VARCHAR(10) PRIMARY KEY, -- Formato compacto YYMMDDHHM
    fecha DATE NOT NULL,          -- Formato YYYY-MM-DD
    hora TIME NOT NULL,           -- Formato HH:MM
    anotaciones TEXT,
    id_cliente INT NOT NULL,
    id_servicio INT NOT NULL,
    id_usuario_gestor INT NOT NULL, -- Quién registró la cita
    creado TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_cliente FOREIGN KEY (id_cliente) REFERENCES clientes(id),
    CONSTRAINT fk_servicio FOREIGN KEY (id_servicio) REFERENCES servicios(id),
    CONSTRAINT fk_usuario_gestor FOREIGN KEY (id_usuario_gestor) REFERENCES usuarios(id)
);

-- 4. Tabla de Consultas Públicas (Formulario de Contacto Libre)
CREATE TABLE consultas (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    apellido_1 VARCHAR(100),
    apellido_2 VARCHAR(100),
    email VARCHAR(150) NOT NULL, -- No es único (múltiples consultas)
    asunto VARCHAR(200) NOT NULL,
    mensaje TEXT NOT NULL,
    creado TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### 4. Lógica de Negocio y Seguridad (Backend FastAPI)

## 4.1. Criptografía y Control de Identidades

Haseho Obligatorio (SHA-256): Queda terminantemente prohibido almacenar contraseñas en texto plano o bajo algoritmos inseguros/obsoletos como MD5. Las credenciales de acceso deben procesarse utilizando hashlib.sha256() con codificación UTF-8 antes de la persistencia en la base de datos de Supabase.

Protección de Rutas por Token (JWT): Toda mutación (inserción, actualización, borrado) sobre las citas de la agenda requerirá la inyección y validación de la cabecera HTTP Authorization: Bearer <JWT_TOKEN>.

Privilegios Administrativos: El endpoint POST /auth/register no tendrá interfaz gráfica disponible en el login. Estará protegido por el middleware de seguridad para que únicamente un usuario con credenciales de administrador previas pueda dar de alta a nuevos empleados o gestores.

## 4.2. Control de Concurrencia y Bloqueo Pesimista

Para mitigar condiciones de carrera (Race Conditions) e impedir que dos gestores en escritorios concurrentes reserven o modifiquen la misma franja horaria de forma simultánea, el backend forzará un bloqueo exclusivo a nivel de fila mediante with_for_update().

```Python
# Ubicación requerida: servidores/routers/eventos.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from database import get_db
from models import Evento, UserAuth

router = APIRouter(prefix="/eventos", tags=["Eventos"])

@router.post("/", status_code=status.HTTP_201_CREATED)
def agendar_cita(
    evento_data: Evento,
    db: Session = Depends(get_db),
    current_user: UserAuth = Depends(get_current_user) # Capa de Seguridad Inyectada
):
    # Forzar estrategia de Bloqueo Pesimista en motor PostgreSQL (Supabase)
    statement = select(Evento).where(Evento.id == evento_data.id).with_for_update()
    registro_bloqueado = db.exec(statement).first()

    if registro_bloqueado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Operación rechazada. La franja horaria seleccionada ya ha sido asignada en otra transacción concurrente."
        )

    # Inyección automática del ID del gestor autenticado
    evento_data.id_usuario_gestor = current_user.id

    db.add(evento_data)
    db.commit()
    db.refresh(evento_data)
    return {"status": "success", "data": evento_data}
```

### 5. Arquitectura del Frontend y Sincronización Asíncrona

El cliente web migrará por completo de estructuras localStorage a flujos reactivos basados en el consumo de la API de Nginx (/api/).

## 5.1. Reglas Horarias e Identificación Estética

- Horario Operativo: Bloques fijos e inmutables de 1 hora distribuidos entre las 08:00 y las 14:00.
- Al seleccionar o alternar una fecha en la interfaz de usuario, el script ejecutará una llamada asíncrona: fetch('/api/eventos/dia?fecha=YYYY-MM-DD').
- El bucle de renderizado mapeará los datos devueltos por el backend. Si una franja horaria posee un registro asignado con su correspondiente ID de tiempo (YYMMDDHHM), el nodo del DOM adoptará obligatoriamente la clase CSS .locked (deshabilitando clics adicionales y mostrando el resumen de la cita). De lo contrario, se renderizará con la clase .available, habilitando el formulario modal de registro.

## 5.2. Desagregación de Formularios

El formulario modal para agendar citas se adaptará al nuevo modelo estructurado relacional, dividiendo el campo genérico anterior en inputs específicos:

- input[name="nombre"] (Obligatorio)
- input[name="apellido_1"] (Obligatorio)
- input[name="apellido_2"] (Opcional)
- input[name="dni"] (Obligatorio, con máscara de validación)
- input[name="email"] (Obligatorio, formato de correo)
- input[name="telefono"] (Obligatorio)
- select[name="id_servicio"] -> El elemento selector se poblará en caliente recorriendo los datos obtenidos de la petición inicial fetch('/api/servicios'), extrayendo los nombres y precios reales parametrizados en Supabase.

### 6. Git Flow y Exclusiones de Construcción

Para mantener la integridad y la seguridad del repositorio común en Git, queda prohibida la subida de entornos locales, certificados locales o secretos corporativos.

Archivo .gitignore (Raíz del proyecto)

```Plaintext
# Secretos y Entornos
.env
nginx/certs/*.crt
nginx/certs/*.key

# Intérprete y Caché de Python
__pycache__/
*.py[cod]
*$py.class
.venv/
env/
venv/
.pytest_cache/

# Configuraciones de Entornos de Desarrollo (IDEs)
.idea/
.vscode/
*.suo
*.workspace
```

Archivo .dockerignore (Raíz del proyecto)

```Plaintext
.git
.gitignore
.dockerignore
.idea
.vscode
servidor/.venv
servidor/env
README.md
```

### 7. Instrucciones de Asignación Inmediata de Tareas

- Ingeniero DevOps / Backend Core (Dev 1): Generar los certificados autofirmados HTTPS locales dentro de ./nginx/certs/, estructurar la inicialización del motor FastAPI con soporte CORS/Uvicorn y disponibilizar las rutas base de autenticación basadas en SHA-256 y firma JWT.

- Desarrollador Frontend Core (Dev 2): Desacoplar por completo las llamadas de almacenamiento local de app.js. Diseñar el interceptor de peticiones asíncronas (fetch) para capturar el token de sesión, almacenarlo de forma segura en sessionStorage e inyectarlo en las cabeceras de autorización de la agenda.

### Resumen de los puntos clave incluidos en el archivo:

1. **Flujo y Aislamiento Perimetral:** Explicación detallada de cómo Nginx en el puerto `9090` (HTTPS) actúa como proxy y protege por completo el contenedor de FastAPI en la red interna de Docker (`cypher_network`).
2. **Orquestación Limpia:** Códigos de configuración completos para `docker-compose.yml`, `.env` y el archivo `nginx.conf`, preparados para desarrollo en `localhost` y escalables para tu URL DDNS con No-IP.
3. **Migración a Supabase (PostgreSQL):** El modelo DDL de base de datos adaptado para Postgres en la nube, respetando la estructura relacional de las tablas `usuarios`, `servicios`, `eventos` (con la Primary Key string compacta `YYMMDDHHM`) y `consultas`.
4. **Seguridad y Criptografía:** Bloques de código de ejemplo para FastAPI aplicando la inyección del Token JWT y forzando la estrategia de **Bloqueo Pesimista** (`with_for_update()`) para anular colisiones por lecturas sucias concurrentes, además de obligar el hasheo de contraseñas bajo **SHA-256**.
5. **Git Flow y Control:** Se integran las configuraciones exactas listas para copiar de los archivos `.gitignore` y `.dockerignore` para mantener limpio tu repositorio.
