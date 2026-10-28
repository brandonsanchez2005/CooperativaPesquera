from django.urls import path

from . import views


urlpatterns = [
    path("camaras/", views.camaras_api, name="camaras_api"),
    path("camaras/<int:id>/", views.camara_detalle_api, name="camara_detalle_api"),
    path("lotes/", views.lotes_api, name="lotes_api"),
    path("lotes/<int:id>/", views.lote_detalle_api, name="lote_detalle_api"),
    path("alertas/", views.alertas_api, name="alertas_api"),
]