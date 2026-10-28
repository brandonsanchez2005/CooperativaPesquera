from django.contrib import admin
from .models import Cliente, PrecioSemanal, Pedido, DetallePedido

admin.site.register(Cliente)
admin.site.register(PrecioSemanal)
admin.site.register(Pedido)
admin.site.register(DetallePedido)