# Módulos de Inventario y Procesamiento

## Propósito

Inventario registra las cámaras frías y los lotes de producto que llegan de las
capturas. Procesamiento registra cuánto producto se transforma y cuánto producto
final se obtiene.

## Relaciones

- Una captura puede generar uno o varios lotes de inventario.
- Una cámara fría puede almacenar varios lotes.
- Un lote de inventario puede utilizarse en varios procesamientos.
- Cada procesamiento indica la presentación obtenida, como filete o posta.
- La existencia disponible de un lote se calcula restando los kilogramos
  procesados a sus kilogramos iniciales.
- La merma se calcula restando los kilogramos obtenidos a los procesados.

## Endpoints

### Inventario

- `GET` y `POST /api/inventario/camaras/`
- `GET`, `PUT`, `PATCH` y `DELETE /api/inventario/camaras/<id>/`
- `GET` y `POST /api/inventario/lotes/`
- `GET`, `PUT`, `PATCH` y `DELETE /api/inventario/lotes/<id>/`
- `GET /api/inventario/alertas/`: lotes disponibles que vencen dentro de los
  próximos dos días o que ya vencieron.

### Procesamiento

- `GET` y `POST /api/procesamiento/`
- `GET`, `PUT`, `PATCH` y `DELETE /api/procesamiento/<id>/`

Los listados están paginados y aceptan `?page=`.
Las solicitudes de escritura aceptan JSON.

## Filtros y consultas

En lotes se pueden combinar los parámetros `captura`, `camara` y `especie`.
También se admite búsqueda por código, especie o cámara, ordenamiento por fecha
de ingreso o vencimiento y paginación.

En procesamiento se pueden combinar `lote`, `producto` y `especie`.
También se admite búsqueda por producto o especie, ordenamiento por fecha y
paginación.

## Reglas de negocio

1. La cámara debe estar activa para recibir un lote.
2. La temperatura de la cámara no puede superar la temperatura máxima de la
   especie almacenada.
3. La fecha de vencimiento debe ser posterior a la fecha de ingreso.
4. Los kilogramos almacenados no pueden superar los de la captura.
5. La cantidad en la cámara no puede superar su capacidad.
6. La cantidad inicial de un lote no puede ser menor que la ya procesada.
7. La fecha de procesamiento debe estar entre el ingreso y el vencimiento.
8. Los kilogramos procesados deben ser positivos y no superar la existencia.
9. Los kilogramos obtenidos deben ser positivos y no superar los procesados.
10. El PATCH debe aplicar las mismas validaciones que la creación.

## Permisos

Todas las rutas requieren token.

- Administrador: consulta, crea, actualiza y elimina.
- Operador: consulta, crea y actualiza.
- Consulta: consulta lotes y procesamientos relacionados con su pescador;
  puede consultar cámaras, pero no crear, actualizar ni eliminar.

## Consultas ORM

Los listados usan `select_related` para cargar las relaciones principales.
La existencia disponible se obtiene con una agregación `Sum` de los
kilogramos procesados asociados al lote.