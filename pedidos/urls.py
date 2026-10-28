from django.urls import path
from . import views

urlpatterns = [
    path("clientes/", views.clientes_api, name="clientes_api"),
    path("clientes/<int:id>/", views.cliente_detalle_api, name="cliente_detalle_api"),
    path("precios/", views.precios_api, name="precios_api"),
    path("precios/<int:id>/", views.precio_detalle_api, name="precio_detalle_api"),
    path("ordenes/", views.pedidos_api, name="pedidos_api"),
    path("ordenes/<int:id>/", views.pedido_detalle_api, name="pedido_detalle_api"),
    path("detalles/", views.detalles_api, name="detalles_api"),
    path(
        "detalles/<int:id>/",
        views.detalle_pedido_detalle_api,
        name="detalle_pedido_detalle_api",
    ),
]