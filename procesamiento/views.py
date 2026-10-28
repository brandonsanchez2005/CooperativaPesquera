from rest_framework.decorators import api_view

from faenas.views import detalle_recurso, listar_recurso, obtener_rol
from .models import Procesamiento
from .serializers import ProcesamientoSerializer


def procesamientos_visibles(request):
    datos = Procesamiento.objects.select_related(
        "lote_inventario",
        "lote_inventario__captura",
        "lote_inventario__captura__especie",
        "lote_inventario__camara",
    )

    if obtener_rol(request.user) == "Consulta":
        datos = datos.filter(
            lote_inventario__captura__faena__pescador__usuario=request.user
        )

    return datos


@api_view(["GET", "POST"])
def procesamientos_api(request):
    return listar_recurso(
        request,
        Procesamiento,
        ProcesamientoSerializer,
        queryset=procesamientos_visibles(request),
        filtros={
            "lote": "lote_inventario_id",
            "producto": "producto",
            "especie": "lote_inventario__captura__especie_id",
        },
        campos_busqueda=[
            "producto",
            "lote_inventario__captura__especie__nombre",
        ],
        campos_ordenamiento=["fecha_procesamiento", "producto"],
        ordenamiento_default="-fecha_procesamiento",
    )


@api_view(["GET", "PUT", "PATCH", "DELETE"])
def procesamiento_detalle_api(request, id):
    return detalle_recurso(
        request,
        Procesamiento,
        ProcesamientoSerializer,
        id,
        queryset=procesamientos_visibles(request),
    )