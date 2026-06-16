Para evitar las lecturas sucias y bloquear las filas mientras una transacción las está modificando (impidiendo que otra conexión las edite o las borre a la vez), la solución técnica no está en los permisos de Docker, sino en los Niveles de Aislamiento y en los Bloqueos de la propia base de datos (MariaDB/InnoDB).

También para evitar las "lecturas sucias" (Dirty Reads), la teoría de bases de datos nos dice que necesitamos, como mínimo, un nivel de aislamiento llamado Read Committed o, para ir sobre seguro en entornos transaccionales, Repeatable Read (que es el que MariaDB trae activado por defecto).

Aquí tenemos dos opciones reales para plantear en el proyecto, atacando la base de datos:

### Opción 1.1: Subir el Nivel de Aislamiento a SERIALIZABLE

Por defecto, MariaDB usa REPEATABLE READ, que evita lecturas sucias pero permite cierta concurrencia. Si subes el nivel a SERIALIZABLE, la base de datos se vuelve estrictamente síncrona.

- Cómo funciona: Cuando la transacción A haga un SELECT, INSERT o UPDATE sobre un conjunto de datos, MariaDB bloquea por completo esos registros. Si la transacción B (la app u otra terminal) intenta actualizar o eliminar esos mismos datos en ese instante, se queda "en espera" (congelada) hasta que la transacción A haga COMMIT o ROLLBACK.

Cómo se aplica en MariaDB:

```SQL
SET GLOBAL TRANSACTION ISOLATION LEVEL SERIALIZABLE;
```

### Opción 1.2: Bloqueo Explícito en las Consultas (FOR UPDATE)

Si no quieres ralentizar toda la base de datos con el nivel anterior, puedes bloquear las transacciones de forma quirúrgica desde el código de la app usando Bloqueo Pesimista.

- Cómo funciona: Cuando la app va a realizar una operación crítica, hace la lectura añadiendo FOR UPDATE al final. Esto le dice a MariaDB: "Voy a modificar esto, bloquea estas filas inmediatamente para cualquier otra transacción de inserción, actualización o borrado".

Ejemplo en SQL:

```SQL
START TRANSACTION;
-- Esto bloquea al usuario 5. Si otra conexión intenta un UPDATE o DELETE aquí, se bloquea.
SELECT * FROM usuarios WHERE id = 5 FOR UPDATE;

-- Aquí haces tus operaciones de forma segura...
UPDATE usuarios SET saldo = 100 WHERE id = 5;
COMMIT; -- Aquí se libera el bloqueo para los demás.
```

### Opción 1.3: El enfoque "Anti-Borrado" del Profesor (Permisos de Usuario)

Si el problema del proyecto es que el profesor entró por terminal y ejecutó un DROP DATABASE o un DELETE masivo rompiendo la app, la forma de bloquear eso en producción es capar al usuario que usa la app.

- La app nunca debe conectarse a la base de datos como root. Debes crear un usuario exclusivo para la app que solo tenga permisos de escritura y lectura de registros, pero que tenga prohibido borrar tablas o bases de datos:

```SQL
-- Crear usuario de la app con permisos justos (sin DROP ni ALTER)
CREATE USER 'user_app'@'%' IDENTIFIED BY 'clave_segura';
GRANT SELECT, INSERT, UPDATE, DELETE ON bbdd_app.* TO 'user_app'@'%';
FLUSH PRIVILEGES;
```

De esta forma, si alguien compromete la app o intenta lanzar un comando de destrucción de estructuras desde ese usuario, la base de datos rechazará la transacción automáticamente.

### En el código de la app

Sin embargo, para bloquear físicamente una transacción mientras otra está modificando, insertando o eliminando el mismo registro, tenemos que implementar Bloqueos Concurrenciales (Locking) en tu código de FastAPI con SQLModel.

Aquí tienes las dos mejores formas de resolverlo directamente en tus scripts de Python:

### Opción 2.1: Bloqueo Pesimista (with_for_update) — La más segura

El bloqueo pesimista asume que "algo va a salir mal" y que es muy probable que otro usuario intente machacar los datos.

Cuando una ruta de tu FastAPI vaya a actualizar o eliminar un registro, le añade la instrucción .with_for_update(). Esto le dice a MariaDB: "Oye, voy a leer a este registro para cambiarlo. Ponle un candado a su fila. Si otra transacción intenta leerlo, actualizarlo o borrarlo, hazla esperar en cola hasta que yo haga session.commit()".

- Cómo se aplica en tu código de FastAPI:
  Cuando programes la ruta de actualización o borrado en tu archivo .py, hazlo así:

```Python
statement = select(Registro).where(Registro.id == registro_id).with_for_update()
```

- ¿Qué pasa con las inserciones?
  Si bloqueas una fila que ya existe, no afecta a las inserciones de nuevos alumnos. Pero si quieres evitar que se inserten alumnos duplicados en una tabla mientras consultas (lecturas fantasma), MariaDB gestiona esto bloqueando el índice de forma automática mediante Next-Key Locks.

### Opción 2.2: Asegurar el Nivel de Aislamiento Global en la Conexión

Para dormir totalmente tranquilo y asegurar que ninguna sesión de tu app pueda hacer jamás una lectura sucia bajo ninguna circunstancia, puedes forzar el nivel de aislamiento directamente en la raíz, cuando creas el engine en tu archivo .py.

Modifica la creación de tu motor añadiendo el parámetro isolation_level:

```Python
# Forzamos REPEATABLE READ (Evita lecturas sucias y lecturas no repetibles)
engine = create_engine(
    DATABASE_URL,
    isolation_level="REPEATABLE READ"
)
```
