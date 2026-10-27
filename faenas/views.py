from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import (
    Pescador,
    Embarcacion,
    Especie,
    Faena,
    Captura,
)
from .serializers import (
    PescadorSerializer,
    EmbarcacionSerializer,
    EspecieSerializer,
    FaenaSerializer,
    CapturaSerializer,
)


def obtener_rol(usuario):
    if usuario.is_superuser:
        return "Administrador"

    grupos = usuario.groups.values_list("name", flat=True)

    if "Administrador" in grupos:
        return "Administrador"

    if "Operador" in grupos:
        return "Operador"

    if "Consulta" in grupos:
        return "Consulta"

    return None


# -------------------------------------------------------------------------------


def aplicar_filtro_consulta(queryset, rol, usuario, alcance):

    if rol != "Consulta":
        return queryset

    if alcance == "pescador":
        return queryset.filter(usuario=usuario)

    if alcance == "faena":
        return queryset.filter(pescador__usuario=usuario)

    if alcance == "captura":
        return queryset.filter(faena__pescador__usuario=usuario)

    return queryset


# -------------------------------------------------------------------------------


def listar_recurso(
    request,
    modelo,
    serializer_class,
    queryset=None,
    alcance=None,
    filtros=None,
    campos_busqueda=None,
    campos_ordenamiento=None,
    ordenamiento_default=None,
):
    rol = obtener_rol(request.user)

    if rol is None:
        return Response(
            {"detail": "No tiene un perfil autorizado."},
            status=status.HTTP_403_FORBIDDEN,
        )

    if request.method == "GET":
        datos = queryset if queryset is not None else modelo.objects.all()
        datos = aplicar_filtro_consulta(datos, rol, request.user, alcance)

        for parametro, campo in (filtros or {}).items():
            valor = request.query_params.get(parametro)
            if valor:
                datos = datos.filter(**{campo: valor})

        texto = request.query_params.get("search")
        if texto and campos_busqueda:
            condicion = Q()
            for campo in campos_busqueda:
                condicion |= Q(**{f"{campo}__icontains": texto})
            datos = datos.filter(condicion)

        orden = request.query_params.get("ordering")
        if orden and campos_ordenamiento:
            campo_solicitado = orden.lstrip("-")
            if campo_solicitado in campos_ordenamiento:
                datos = datos.order_by(orden)
            elif ordenamiento_default:
                datos = datos.order_by(ordenamiento_default)
        elif ordenamiento_default:
            datos = datos.order_by(ordenamiento_default)

        paginador = Paginator(datos, 5)
        pagina = paginador.get_page(request.query_params.get("page", 1))

        return Response({
            "pagina_actual": pagina.number,
            "total_paginas": paginador.num_pages,
            "total_registros": paginador.count,
            "resultados": serializer_class(
                pagina.object_list, many=True
            ).data,
        })

    if rol not in ["Administrador", "Operador"]:
        return Response(
            {"detail": "Se requiere perfil Operador o Administrador."},
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = serializer_class(data=request.data)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -------------------------------------------------------------------------------


def detalle_recurso(request, modelo, serializer_class, id, queryset=None, alcance=None):
    rol = obtener_rol(request.user)

    if rol is None:
        return Response(
            {"detail": "No tiene un perfil autorizado."},
            status=status.HTTP_403_FORBIDDEN,
        )

    datos = queryset if queryset is not None else modelo.objects.all()
    datos = aplicar_filtro_consulta(datos, rol, request.user, alcance)
    objeto = get_object_or_404(datos, id=id)

    if request.method == "GET":
        return Response(serializer_class(objeto).data)

    if request.method in ["PUT", "PATCH"]:
        if rol not in ["Administrador", "Operador"]:
            return Response(
                {"detail": "Se requiere perfil Operador o Administrador."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = serializer_class(
            objeto, data=request.data, partial=request.method == "PATCH"
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == "DELETE":
        if rol != "Administrador":
            return Response(
                {"detail": "Solo el Administrador puede eliminar."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            objeto.delete()
        except ProtectedError:
            return Response(
                {"detail": "No se puede eliminar porquetiene registros relacionados."},
                status=status.HTTP_409_CONFLICT,
            )
    return Response(status=status.HTTP_204_NO_CONTENT)


# -------------------------------------------------------------------------------


@api_view(["GET", "POST"])
def pescadores_api(request):
    return listar_recurso(
        request,
        Pescador,
        PescadorSerializer,
        alcance="pescador",
        campos_busqueda=["nombre", "identificacion"],
        campos_ordenamiento=["nombre", "identificacion"],
        ordenamiento_default="nombre",
    )


# -------------------------------------------------------------------------------


@api_view(["GET", "PUT", "PATCH", "DELETE"])
def pescador_detalle_api(request, id):
    return detalle_recurso(
        request, Pescador, PescadorSerializer, id, alcance="pescador"
    )


# -------------------------------------------------------------------------------


@api_view(["GET", "POST"])
def embarcaciones_api(request):
    return listar_recurso(
        request,
        Embarcacion,
        EmbarcacionSerializer,
        campos_busqueda=["nombre", "matricula"],
        campos_ordenamiento=["nombre", "matricula"],
        ordenamiento_default="nombre",
    )


# -------------------------------------------------------------------------------


@api_view(["GET", "PUT", "PATCH", "DELETE"])
def embarcacion_detalle_api(request, id):
    return detalle_recurso(request, Embarcacion, EmbarcacionSerializer, id)


# -------------------------------------------------------------------------------


@api_view(["GET", "POST"])
def especies_api(request):
    return listar_recurso(
        request,
        Especie,
        EspecieSerializer,
        campos_busqueda=["nombre"],
        campos_ordenamiento=["nombre"],
        ordenamiento_default="nombre",
    )


# -------------------------------------------------------------------------------


@api_view(["GET", "PUT", "PATCH", "DELETE"])
def especie_detalle_api(request, id):
    return detalle_recurso(request, Especie, EspecieSerializer, id)


# -------------------------------------------------------------------------------
@api_view(["GET", "POST"])
def faenas_api(request):
    datos = Faena.objects.select_related("pescador", "embarcacion").prefetch_related(
        "capturas__especie"
    )

    return listar_recurso(
        request,
        Faena,
        FaenaSerializer,
        queryset=datos,
        alcance="faena",
        filtros={
            "pescador": "pescador_id",
            "embarcacion": "embarcacion_id",
            "zona": "zona__icontains",
        },
        campos_busqueda=[
            "pescador__nombre",
            "embarcacion__nombre",
            "zona",
        ],
        campos_ordenamiento=["fecha_salida", "zona"],
        ordenamiento_default="-fecha_salida",
    )


# -------------------------------------------------------------------------------


@api_view(["GET", "PUT", "PATCH", "DELETE"])
def faena_detalle_api(request, id):
    datos = Faena.objects.select_related("pescador", "embarcacion").prefetch_related(
        "capturas__especie"
    )

    return detalle_recurso(
        request, Faena, FaenaSerializer, id, queryset=datos, alcance="faena"
    )


# -------------------------------------------------------------------------------


@api_view(["GET", "POST"])
def capturas_api(request):
    datos = Captura.objects.select_related("faena", "faena__pescador", "especie")

    return listar_recurso(
        request,
        Captura,
        CapturaSerializer,
        queryset=datos,
        alcance="captura",
        filtros={
            "faena": "faena_id",
            "especie": "especie_id",
        },
        campos_busqueda=[
            "especie__nombre",
            "faena__zona",
        ],
        campos_ordenamiento=["kilogramos", "precio_kg"],
        ordenamiento_default="-kilogramos",
    )


# -------------------------------------------------------------------------------


@api_view(["GET", "PUT", "PATCH", "DELETE"])
def captura_detalle_api(request, id):
    datos = Captura.objects.select_related("faena", "faena__pescador", "especie")

    return detalle_recurso(
        request, Captura, CapturaSerializer, id, queryset=datos, alcance="captura"
    )


# -------------------------------------------------------------------------------


@api_view(["GET"])
def resumen_capturas_api(request):
    rol = obtener_rol(request.user)

    if rol is None:
        return Response(
            {"detail": "No tiene un perfil autorizado."},
            status=status.HTTP_403_FORBIDDEN,
        )

    datos = Captura.objects.all()

    if rol == "Consulta":
        datos = datos.filter(faena__pescador__usuario=request.user)

    resumen = (
        datos.values("especie__nombre")
        .annotate(
            kilogramos_totales=Sum("kilogramos"),
            cantidad_capturas=Count("id"),
        )
        .order_by("-kilogramos_totales")
    )

    return Response(list(resumen))
