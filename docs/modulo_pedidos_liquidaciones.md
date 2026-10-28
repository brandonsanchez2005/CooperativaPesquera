# Módulos de Pedidos y Liquidaciones

## Propósito

Pedidos registra clientes mayoristas, precios semanales y ventas de productos
obtenidos mediante Procesamiento.

Liquidaciones calcula el monto bruto de las capturas de una faena, registra
gastos financiados por la cooperativa y muestra el monto neto correspondiente
al pescador.

## Relaciones

- Un cliente puede tener varios pedidos.
- Un pedido puede incluir varios detalles.
- Cada detalle se relaciona con un procesamiento y registra los kilogramos
  vendidos y el precio por kilogramo vigente al realizar el pedido.
- Una especie y una presentación pueden tener distintos precios según el
  periodo de vigencia.
- Una faena puede tener varios gastos financiados.
- Cada faena puede tener una sola liquidación.

## Endpoints de Pedidos

- `GET` y `POST /api/pedidos/clientes/`
- `GET`, `PUT`, `PATCH` y `DELETE /api/pedidos/clientes/<id>/`
- `GET` y `POST /api/pedidos/precios/`
- `GET`, `PUT`, `PATCH` y `DELETE /api/pedidos/precios/<id>/`
- `GET` y `POST /api/pedidos/ordenes/`
- `GET`, `PUT`, `PATCH` y `DELETE /api/pedidos/ordenes/<id>/`
- `GET` y `POST /api/pedidos/detalles/`
- `GET`, `PUT`, `PATCH` y `DELETE /api/pedidos/detalles/<id>/`

## Endpoints de Liquidaciones

- `GET` y `POST /api/liquidaciones/gastos/`
- `GET`, `PUT`, `PATCH` y `DELETE /api/liquidaciones/gastos/<id>/`
- `GET` y `POST /api/liquidaciones/`
- `GET`, `PUT`, `PATCH` y `DELETE /api/liquidaciones/<id>/`

Los listados aceptan `?page=` y devuelven cinco registros por página.
Todas las rutas requieren token.

## Reglas de Pedidos

1. No se crean pedidos para clientes inactivos.
2. Los precios deben ser mayores que cero y su fecha final no puede preceder
   a la fecha inicial.
3. No puede haber periodos de precio solapados para la misma especie y
   presentación.
4. El detalle usa el precio semanal vigente para la especie, presentación y
   fecha del pedido.
5. El precio queda guardado en el detalle como referencia histórica.
6. Los kilogramos solicitados no pueden superar los kilogramos obtenidos en
   Procesamiento menos las cantidades ya reservadas en pedidos no cancelados.
7. No se agregan detalles a pedidos cancelados o entregados.
8. Un pedido cancelado no se puede reactivar.
9. No se puede entregar un pedido sin detalles.

## Reglas de Liquidaciones

1. La faena debe tener capturas para generar una liquidación.
2. El monto bruto suma kilogramos por precio de cada captura.
3. Los gastos financiados deben ser positivos.
4. Los gastos acumulados no pueden superar el monto bruto.
5. El monto neto es el monto bruto menos los gastos.
6. Una faena solo puede tener una liquidación.
7. No se pueden modificar gastos asociados a una liquidación pagada.
8. Una liquidación pagada no se puede modificar.

## Cálculos

- Monto bruto: suma de `captura.kilogramos * captura.precio_kg`.
- Total de gastos: suma de los gastos registrados para la faena.
- Monto neto: monto bruto menos total de gastos.
- Total de pedido: suma de `detalle.kilogramos * detalle.precio_kg`.

## Permisos

- Administrador: consulta, crea, actualiza y elimina.
- Operador: consulta, crea y actualiza.
- Consulta: no accede a clientes, precios ni pedidos; puede consultar gastos y
  liquidaciones de sus propias faenas.

Las escrituras se hacen con `Authorization: Token <token>`.