Aquí tienes el resumen real, directo y sin rodeos de todo lo que hemos tocado en esta sesión:

1. Conceptos Teóricos y Arquitectura
Pérdida de datos en JSON: Analizamos cómo el viaje de datos vía HTTP (JSON) destruye la orientación a objetos (métodos, prototipos), la identidad referencial en memoria, y fuerza a que todas las claves sean strings.

Integridad lógica (Python/JS): Explicamos el peligro de enviar Tuplas o Conjuntos (set) a JavaScript. Al viajar por la red se transforman en Arrays, y al volver al backend de Python entran como listas (list), lo que rompe la unicidad (duplicados en BD) o genera excepciones de tipo (TypeError: unhashable type: 'list') si intentas usarlas como claves de diccionario.

Seguridad de Secretos en Cloud: Desgranamos la estrategia Zero Trust para infraestructuras distribuidas: uso de .gitignore + Gitleaks para el código, inyección en memoria RAM (tmpfs) en Kubernetes, uso de Gestores de Secretos (Vault, AWS) con rotación automática, eliminación de contraseñas usando IAM Roles, y cifrado en tránsito con TLS 1.3 / mTLS.

Protección de Contraseñas de Usuarios: Detallamos que las claves de usuarios nunca se descifran. Se protegen usando hashing criptográfico unidireccional y lento (Argon2id o Bcrypt) combinado con una Sal (Salt) aleatoria por usuario para reventar ataques de tablas de arcoíris.

2. Resolución de Preguntas de Examen (FastAPI / Web)
FastAPI + Jinja2 (SSR): Confirmamos que las plantillas se procesan al 100% en el servidor Python. Las funciones de formato como esPremium o formatearFecha se deben registrar previamente en el entorno de Jinja2 antes de enviar el HTML cocinado al navegador.

Consumo de APIs con Fetch: Recordamos que la sintaxis correcta en JavaScript para extraer el cuerpo de una respuesta JSON es const datos = await respuesta.json(); (requiere doble await por el manejo de streams de red).

Validación con SQLModel: Aclaramos que al heredar directamente de Pydantic, la validación de campos (regex, ge, le) ocurre de forma automática al instanciar el objeto en los parámetros de la ruta, mucho antes de que intervenga la sesión de la base de datos.

Parámetros HTTP (GET vs POST): Ratificamos que en FastAPI los tipos primitivos en rutas GET se leen automáticamente como Query Params en la URL (?q=busqueda), mientras que los modelos complejos en POST se extraen del cuerpo del JSON de la petición.

3. Entorno de Desarrollo y Debugging
El gestor uv: Presentamos esta herramienta de Astral escrita en Rust que reemplaza a pip y virtualenv, multiplicando por 100 la velocidad de instalación y ejecución (uv run). Dejamos claros los comandos para instalarlo en sistemas Unix y Windows.

Error de importación en Uvicorn: Solucionamos el petardazo TypeError: the 'package' argument is required... provocado por pasarle a Uvicorn una ruta de archivo con barras de sistema operativo (.\main_facultad_3:app). Se corrigió usando la sintaxis de módulo de Python: main_facultad_3:app.

Configuración del PATH: Agregamos el binario de uv al entorno de Git Bash (source $HOME/.local/bin/env) y explicamos cómo persistir la ruta C:\Users\Victor\.local\bin en las Variables de Entorno de Windows para que responda también en PowerShell y CMD.

Ademas del contenido de este curso: https://github.com/Asabeneh/30-Days-Of-Python/tree/master/Spanish