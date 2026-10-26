from django.urls import path
from . import views

urlpatterns = [
    path("pescadores/", views.pescadores_api, name="pescadores_api"),
    path(
        "pescadores/<int:id>/", views.pescador_detalle_api, name="pescador_detalle_api"
    ),
    path("embarcaciones/", views.embarcaciones_api, name="embarcaciones_api"),
    path(
        "embarcaciones/<int:id>/",
        views.embarcacion_detalle_api,
        name="embarcacion_detalle_api",
    ),
    path("especies/", views.especies_api, name="especies_api"),
    path("especies/<int:id>/", views.especie_detalle_api, name="especie_detalle_api"),
    path(
        "faenas/resumen-capturas/",
        views.resumen_capturas_api,
        name="resumen_capturas_api",
    ),
    path("faenas/", views.faenas_api, name="faenas_api"),
    path("faenas/<int:id>/", views.faena_detalle_api, name="faena_detalle_api"),
    path("capturas/", views.capturas_api, name="capturas_api"),
    path("capturas/<int:id>/", views.captura_detalle_api, name="captura_detalle_api"),
]
