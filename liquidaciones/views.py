from rest_framework.decorators import api_view

from faenas.views import detalle_recurso, listar_recurso, obtener_rol
from .models import GastoFaena, Liquidacion
from .serializers import GastoFaenaSerializer, LiquidacionSerializer

def gastos_visibles(request):
    datos = GastoFaena.objects.select_related(
        "faena",
        "faena__pescador",
    ).prefetch_related("faena__capturas")

    if obtener_rol(request.user) == "Consulta":
        datos = datos.filter(faena__pescador__usuario=request.user)

    return datos

def liquidaciones_visibles(request):
    datos = Liquidacion.objects.select_related(
        "faena",
        "faena__pescador",
    ).prefetch_related(
        "faena__capturas",
        "faena__gastos",
    )

    if obtener_rol(request.user) == "Consulta":
        datos = datos.filter(faena__pescador__usuario=request.user)

    return datos

@api_view(["GET", "POST"])
def gastos_api(request):
    return listar_recurso(
        request,
        GastoFaena,
        GastoFaenaSerializer,
        queryset=gastos_visibles(request),
        filtros={
            "faena": "faena_id",
            "tipo": "tipo",
        },
        campos_busqueda=["descripcion", "faena__zona"],
        campos_ordenamiento=["fecha", "monto"],
        ordenamiento_default="-fecha",
    )

@api_view(["GET", "PUT", "PATCH", "DELETE"])
def gasto_detalle_api(request, id):
    return detalle_recurso(
        request,
        GastoFaena,
        GastoFaenaSerializer,
        id,
        queryset=gastos_visibles(request),
    )

@api_view(["GET", "POST"])
def liquidaciones_api(request):
    return listar_recurso(
        request,
        Liquidacion,
        LiquidacionSerializer,
        queryset=liquidaciones_visibles(request),
        filtros={
            "faena": "faena_id",
            "estado": "estado",
        },
        campos_busqueda=[
            "faena__pescador__nombre",
            "faena__zona",
        ],
        campos_ordenamiento=["fecha_liquidacion", "estado"],
        ordenamiento_default="-fecha_liquidacion",
    )


@api_view(["GET", "PUT", "PATCH", "DELETE"])
def liquidacion_detalle_api(request, id):
    return detalle_recurso(
        request,
        Liquidacion,
        LiquidacionSerializer,
        id,
        queryset=liquidaciones_visibles(request),
    )