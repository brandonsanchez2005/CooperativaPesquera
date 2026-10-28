from django.urls import path

from . import views


urlpatterns = [
    path("", views.procesamientos_api, name="procesamientos_api"),
    path("<int:id>/", views.procesamiento_detalle_api, name="procesamiento_detalle_api"),
]