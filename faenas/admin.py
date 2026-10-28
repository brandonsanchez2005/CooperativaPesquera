from django.contrib import admin
from .models import Pescador, Embarcacion, Especie, Faena, Captura

admin.site.register(Pescador)
admin.site.register(Embarcacion)
admin.site.register(Especie)
admin.site.register(Faena)
admin.site.register(Captura)