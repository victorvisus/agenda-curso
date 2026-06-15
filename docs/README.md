En paralelo, acerca de la Agenda para servicios, Carlos propone un modelo como el siguiente:
============== AGENDA =====================

# Agenda

Este proyecto sera usado como practica en el curso de kings corner. Principalmente sera realizado un modulo de agenda, el cual consiste en poder crear registros de eventos, citas, etc., bien a traves de un UI de calenario o agenda.

Se tiene pensado agregar otros modulos por temas de practica. A continuación se presenta la arquitectura.

## Diseño de base de datos

Usuarios

- id -> autoincrement, pk
- nombre -> varchar
- apellido_1 -> varchar
- apellido_2 -> varchar
- dni -> varchar, unique
- telefono -> varchar
- email -> varchar, unique

Servicios

- id -> autoincrement, pk
- nombre -> varchar, unique
- descripcion -> varchar
- precio -> float
- activo -> boolean

Citas

- id -> autoincrement, pk
- nombre -> varchar
- descripcion -> varchar, nullable
- fecha_solicitud ->
- fecha_cita ->
- estatus -> enum(pendiente, cancelado, finalizado, en curso)
- id_usuario -> referencia a la tabla Usuarios
- id_servicio -> referencia a la tabla Servicios

Consultas (para informacion y contacto)

- id -> autoincrement, pk
- nombre_usuario -> varchar
- email_usuario -> varchar
- tema_consulta -> varchar
- mensaje -> varchar

> ### Nota(s):
>
> - La tabla consultas es para almacenar la informacion que se pueda hacer a traves de algun formulario de contacto.
> - En este caso, no hace falta que el `email` sea unico, ya que un usuario con el mismo correo puede realizar multiples consultas a traves del tiempo.
> - En relacion al usuario, no haria falta crear una relacion porque en este punto se podria asumir que el usuario no ha pedido alguna cita.
