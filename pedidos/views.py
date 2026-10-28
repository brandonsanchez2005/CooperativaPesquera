from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from faenas.views import (
    detalle_recurso,
    listar_recurso,
    obtener_rol,
)
from .models import Cliente, PrecioSemanal, Pedido, DetallePedido
from .serializers import (
    ClienteSerializer,
    PrecioSemanalSerializer,
    PedidoSerializer,
    DetallePedidoSerializer,
)


def validar_acceso_pedidos(request):
    rol = obtener_rol(request.user)

    if rol not in ["Administrador", "Operador"]:
        return Response(
            {"detail": "Se requiere perfil Operador o Administrador."},
            status=status.HTTP_403_FORBIDDEN,
        )

    return None


@api_view(["GET", "POST"])
def clientes_api(request):
    error = validar_acceso_pedidos(request)
    if error:
        return error

    return listar_recurso(
        request,
        Cliente,
        ClienteSerializer,
        campos_busqueda=["nombre", "identificacion"],
        campos_ordenamiento=["nombre", "identificacion"],
        ordenamiento_default="nombre",
    )


@api_view(["GET", "PUT", "PATCH", "DELETE"])
def cliente_detalle_api(request, id):
    error = validar_acceso_pedidos(request)
    if error:
        return error

    return detalle_recurso(
        request, Cliente, ClienteSerializer, id
    )


@api_view(["GET", "POST"])
def precios_api(request):
    error = validar_acceso_pedidos(request)
    if error:
        return error

    return listar_recurso(
        request,
        PrecioSemanal,
        PrecioSemanalSerializer,
        filtros={
            "especie": "especie_id",
            "producto": "producto",
        },
        campos_busqueda=["especie__nombre", "producto"],
        campos_ordenamiento=["vigente_desde", "precio_kg"],
        ordenamiento_default="-vigente_desde",
    )


@api_view(["GET", "PUT", "PATCH", "DELETE"])
def precio_detalle_api(request, id):
    error = validar_acceso_pedidos(request)
    if error:
        return error

    return detalle_recurso(
        request, PrecioSemanal, PrecioSemanalSerializer, id
    )


@api_view(["GET", "POST"])
def pedidos_api(request):
    error = validar_acceso_pedidos(request)
    if error:
        return error

    return listar_recurso(
        request,
        Pedido,
        PedidoSerializer,
        queryset=Pedido.objects.select_related("cliente"),
        filtros={
            "cliente": "cliente_id",
            "estado": "estado",
        },
        campos_busqueda=["cliente__nombre", "cliente__identificacion"],
        campos_ordenamiento=["fecha_pedido", "estado"],
        ordenamiento_default="-fecha_pedido",
    )


@api_view(["GET", "PUT", "PATCH", "DELETE"])
def pedido_detalle_api(request, id):
    error = validar_acceso_pedidos(request)
    if error:
        return error

    return detalle_recurso(
        request,
        Pedido,
        PedidoSerializer,
        id,
        queryset=Pedido.objects.select_related("cliente"),
    )


@api_view(["GET", "POST"])
def detalles_api(request):
    error = validar_acceso_pedidos(request)
    if error:
        return error

    return listar_recurso(
        request,
        DetallePedido,
        DetallePedidoSerializer,
        queryset=DetallePedido.objects.select_related(
            "pedido",
            "procesamiento",
            "procesamiento__lote_inventario",
            "procesamiento__lote_inventario__captura",
            "procesamiento__lote_inventario__captura__especie",
        ),
        filtros={
            "pedido": "pedido_id",
            "procesamiento": "procesamiento_id",
            "producto": "procesamiento__producto",
        },
        campos_busqueda=[
            "pedido__cliente__nombre",
            "procesamiento__producto",
        ],
        campos_ordenamiento=["kilogramos", "precio_kg"],
        ordenamiento_default="-kilogramos",
    )


@api_view(["GET", "PUT", "PATCH", "DELETE"])
def detalle_pedido_detalle_api(request, id):
    error = validar_acceso_pedidos(request)
    if error:
        return error

    return detalle_recurso(
        request,
        DetallePedido,
        DetallePedidoSerializer,
        id,
        queryset=DetallePedido.objects.select_related(
            "pedido",
            "procesamiento",
        ),
    )