from django.urls import path

from . import views

urlpatterns = [
    path("gastos/", views.gastos_api, name="gastos_api"),
    path("gastos/<int:id>/", views.gasto_detalle_api, name="gasto_detalle_api"),
    path("", views.liquidaciones_api, name="liquidaciones_api"),
    path(
        "<int:id>/",
        views.liquidacion_detalle_api,
        name="liquidacion_detalle_api",
    ),
]