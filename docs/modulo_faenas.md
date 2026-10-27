# Módulo de Faenas y Capturas

## Propósito

Registrar las salidas de pesca de los pescadores asociados a la cooperativa y
las especies y cantidades capturadas durante cada faena.

## Relaciones

- Un pescador puede registrar varias faenas.
- Una embarcación puede participar en varias faenas.
- Una faena puede registrar varias especies y una especie puede aparecer en
varias faenas.
- El modelo Captura representa la relación entre Faena y Especie y almacena
kilogramos y precio por kilogramo.
- Las relaciones históricas usan PROTECT para evitar borrar información
referenciada.

## Endpoints

Para los recursos de pescadores, embarcaciones, especies, faenas y capturas:
- `GET /api/<recurso>/`: lista paginada.
- `POST /api/<recurso>/`: crea un registro.
- `GET /api/<recurso>/<id>/`: consulta el detalle.
- `PUT` o `PATCH /api/<recurso>/<id>/`: actualiza.
- `DELETE /api/<recurso>/<id>/`: elimina si no existen registros protegidos.

También está disponible:
- `GET /api/faenas/resumen-capturas/`: kilogramos y cantidad de capturas por especie.

Todas las rutas de negocio requieren un token enviado como `Authorization: Token <token>`.

## Filtros y consultas

En `/api/faenas/` se pueden combinar `pescador`, `embarcacion` y `zona`.
También se admite `search`, `ordering` y `page`. Los listados muestran cinco registros por página.
En `/api/capturas/` se pueden combinar `faena` y `especie`, además de usar
`search`, `ordering` y `page`.

## Reglas de negocio

1. La fecha de regreso no puede preceder a la fecha de salida.
2. No se permite registrar faenas para pescadores inactivos.
3. No se permite registrar faenas con embarcaciones inactivas.
4. Los kilogramos y el precio por kilogramo deben ser mayores que cero.
5. No se puede registrar una especie inactiva.
6. Una especie no se puede repetir en la misma faena.
7. La suma de capturas de una faena no puede superar la capacidad de su embarcación.
8. Las mismas reglas se verifican al actualizar, incluido PATCH.

## Consultas ORM destacadas

Las listas optimizan el acceso a relaciones usando `select_related` y `prefetch_related`. 
Por ejemplo, el listado de faenas carga el pescador y la embarcación relacionados y precarga sus capturas y especies.
El resumen agrupa las capturas por especie y calcula los kilogramos totales con `Sum` y la cantidad de capturas con `Count`.

## Permisos

- Administrador: puede consultar, crear, actualizar y eliminar.
- Operador: puede consultar, crear y actualizar.
- Consulta: puede consultar sus propias faenas y capturas.