from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from faenas.views import (
    detalle_recurso,
    listar_recurso,
    obtener_rol,
)
from .models import CamaraFria, LoteInventario
from .serializers import CamaraFriaSerializer, LoteInventarioSerializer


def lotes_visibles(request):
    datos = LoteInventario.objects.select_related(
        "captura",
        "captura__faena",
        "captura__especie",
        "camara",
    )

    if obtener_rol(request.user) == "Consulta":
        datos = datos.filter(
            captura__faena__pescador__usuario=request.user
        )

    return datos


@api_view(["GET", "POST"])
def camaras_api(request):
    return listar_recurso(
        request,
        CamaraFria,
        CamaraFriaSerializer,
        campos_busqueda=["nombre", "codigo"],
        campos_ordenamiento=["nombre", "codigo"],
        ordenamiento_default="nombre",
    )


@api_view(["GET", "PUT", "PATCH", "DELETE"])
def camara_detalle_api(request, id):
    return detalle_recurso(
        request,
        CamaraFria,
        CamaraFriaSerializer,
        id,
    )


@api_view(["GET", "POST"])
def lotes_api(request):
    return listar_recurso(
        request,
        LoteInventario,
        LoteInventarioSerializer,
        queryset=lotes_visibles(request),
        filtros={
            "captura": "captura_id",
            "camara": "camara_id",
            "especie": "captura__especie_id",
        },
        campos_busqueda=[
            "codigo",
            "captura__especie__nombre",
            "camara__nombre",
        ],
        campos_ordenamiento=["fecha_ingreso", "fecha_vencimiento"],
        ordenamiento_default="-fecha_ingreso",
    )


@api_view(["GET", "PUT", "PATCH", "DELETE"])
def lote_detalle_api(request, id):
    return detalle_recurso(
        request,
        LoteInventario,
        LoteInventarioSerializer,
        id,
        queryset=lotes_visibles(request),
    )


@api_view(["GET"])
def alertas_api(request):
    rol = obtener_rol(request.user)

    if rol is None:
        return Response(
            {"detail": "No tiene un perfil autorizado."},
            status=status.HTTP_403_FORBIDDEN,
        )

    fecha_limite = timezone.localdate() + timedelta(days=2)
    lotes = lotes_visibles(request).filter(
        fecha_vencimiento__lte=fecha_limite
    )

    lotes_con_existencia = [
        lote for lote in lotes if lote.kilogramos_disponibles > 0
    ]

    return Response(LoteInventarioSerializer(lotes_con_existencia, many=True).data)