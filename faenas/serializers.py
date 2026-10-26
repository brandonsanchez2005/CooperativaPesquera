from decimal import Decimal
from django.db.models import Sum
from rest_framework import serializers
from .models import (
    Pescador,
    Embarcacion,
    Especie,
    Faena,
    Captura,
)

class PescadorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Pescador
        fields = '__all__'

#--------------------------------------------------------------------------------

class EmbarcacionSerializer(serializers.ModelSerializer):

    class Meta:

        model = Embarcacion
        fields = '__all__'

        def validate_capacidad_kg(self, value):

            if value <= 0:
                raise serializers.ValidationError(
                    'La capacidad debe ser mayor que cero.'
                )
            return value

#--------------------------------------------------------------------------------
   
class EspecieSerializer(serializers.ModelSerializer):
    
    class Meta:

        model = Especie
        fields = '__all__'

#--------------------------------------------------------------------------------
    
class FaenaSerializer(serializers.ModelSerializer):

    class Meta:

        model = Faena
        fields = '__all__'

        def validate(self, data):

            fecha_salida = data.get(
                'fecha_salida',
                getattr(self.instance, 'fecha_salida', None)
            )

            fecha_regreso = data.get(
                'fecha_regreso',
                getattr(self.instance, 'fecha_regreso', None)
            )

            pescador = data.get(
                'pescador',
                getattr(self.instance, 'pescador', None)
            )

            embarcacion = data.get(
                'embarcacion',
                getattr(self.instance, 'embarcacion', None)
            )

            if fecha_salida and fecha_regreso and fecha_regreso < fecha_salida:
                raise serializers.ValidationError({
                    'fecha_regreso':'El regreso no puede ser anterior a la salida.'
                })

            if pescador and not pescador.activo:
                raise serializers.ValidationError({
                    'pescador': 'El pescador está inactivo.'
                })
            
            if embarcacion and not embarcacion.activa:
                raise serializers.ValidationError({
                    'embarcacion': 'La embarcación está inactiva.'
                })
            return data

#--------------------------------------------------------------------------------

class CapturaSerializer(serializers.ModelSerializer):

    class Meta:

        model = Captura
        fields = '__all__'

        def validate(self, data):

            faena = data.get(
                'faena',
                getattr(self.instance, 'faena', None)
            )
            especie = data.get(
                'especie',
                getattr(self.instance, 'especie', None)
            )

            kilogramos = data.get(
                'kilogramos',
                getattr(self.instance, 'kilogramos', None)
            )
            
            if especie and not especie.activa:
                raise serializers.ValidationError({
                    'especie': 'La especie está inactiva.'
                })
            
            if kilogramos is None or kilogramos <= Decimal('0'):
                raise serializers.ValidationError({
                    'kilogramos': 'Los kilogramos deben ser mayores que cero.'
                })

            if faena and especie:
                duplicada = Captura.objects.filter(
                    faena=faena,
                    especie=especie
                )

            if self.instance:
                duplicada = duplicada.exclude(pk=self.instance.pk)

            if duplicada.exists():
                raise serializers.ValidationError({
                    'especie':'Esa especie ya está registrada en esta faena.'
                })
            
            if faena and kilogramos:
                capturas_existentes = Captura.objects.filter(faena=faena)

            if self.instance:
                capturas_existentes = capturas_existentes.exclude(
                    pk=self.instance.pk
                )

                total_existente = (
                    capturas_existentes.aggregate(
                        total=Sum('kilogramos')
                    )['total'] or Decimal('0')
                )

                capacidad = faena.embarcacion.capacidad_kg

            if total_existente + kilogramos > capacidad:
                raise serializers.ValidationError({
                    'kilogramos':'La captura supera la capacidad de la embarcación.'
                })
            
            return data