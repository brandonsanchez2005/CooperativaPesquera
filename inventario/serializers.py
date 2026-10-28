from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone
from rest_framework import serializers

from .models import CamaraFria, LoteInventario


def obtener_kilogramos_disponibles(lote):
    procesado = lote.procesamientos.aggregate(
        total=Sum("kilogramos_procesados")
    )["total"] or Decimal("0")

    return lote.kilogramos_iniciales - procesado


class CamaraFriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = CamaraFria
        fields = "__all__"
        
    def validate_capacidad_kg(self, value):
        if value <= Decimal("0"):
            raise serializers.ValidationError("La capacidad debe ser mayor que cero.")
        return value

    def validate(self, data):
        temperatura = data.get(
            "temperatura_actual",
            getattr(self.instance, "temperatura_actual", None),
        )
        activa = data.get("activa", getattr(self.instance, "activa", True))

        if self.instance:
            lotes = self.instance.lotes.select_related("captura__especie")

            for lote in lotes:
                if obtener_kilogramos_disponibles(lote) <= Decimal("0"):
                    continue

                if not activa:
                    raise serializers.ValidationError({
                        "activa": (
                            "No se puede desactivar una cámara con producto disponible."
                        )
                    })

                if temperatura > lote.captura.especie.temperatura_maxima:
                    raise serializers.ValidationError({
                        "temperatura_actual": (
                            "La temperatura supera el máximo de una especie almacenada."
                        )
                    })

        return data


class LoteInventarioSerializer(serializers.ModelSerializer):
    kilogramos_disponibles = serializers.SerializerMethodField()
    estado = serializers.SerializerMethodField()

    class Meta:
        model = LoteInventario
        fields = (
            "id",
            "codigo",
            "captura",
            "camara",
            "fecha_ingreso",
            "fecha_vencimiento",
            "kilogramos_iniciales",
            "kilogramos_disponibles",
            "estado",
        )
        read_only_fields = ("kilogramos_disponibles", "estado")

    def get_kilogramos_disponibles(self, obj):
        return obtener_kilogramos_disponibles(obj)

    def get_estado(self, obj):
        if obj.fecha_vencimiento < timezone.localdate():
            return "VENCIDO"

        if obtener_kilogramos_disponibles(obj) <= Decimal("0"):
            return "AGOTADO"

        return "DISPONIBLE"

    def validate(self, data):
        captura = data.get(
            "captura", getattr(self.instance, "captura", None)
        )
        camara = data.get(
            "camara", getattr(self.instance, "camara", None)
        )
        fecha_ingreso = data.get(
            "fecha_ingreso", getattr(self.instance, "fecha_ingreso", None)
        )
        fecha_vencimiento = data.get(
            "fecha_vencimiento",
            getattr(self.instance, "fecha_vencimiento", None),
        )
        kg_iniciales = data.get(
            "kilogramos_iniciales",
            getattr(self.instance, "kilogramos_iniciales", None),
        )

        if fecha_ingreso and fecha_vencimiento:
            if fecha_vencimiento <= fecha_ingreso:
                raise serializers.ValidationError({
                    "fecha_vencimiento": (
                        "Debe ser posterior a la fecha de ingreso."
                    )
                })

        if kg_iniciales is None or kg_iniciales <= Decimal("0"):
            raise serializers.ValidationError({
                "kilogramos_iniciales": "La cantidad debe ser mayor que cero."
            })

        if captura and camara:
            especie = captura.especie

            if not camara.activa:
                raise serializers.ValidationError({
                    "camara": "No se puede usar una cámara inactiva."
                })

            if camara.temperatura_actual > especie.temperatura_maxima:
                raise serializers.ValidationError({
                    "camara": (
                        "La temperatura supera el máximo permitido para la especie."
                    )
                })

            lotes_captura = LoteInventario.objects.filter(captura=captura)
            lotes_camara = LoteInventario.objects.filter(camara=camara)

            if self.instance:
                lotes_captura = lotes_captura.exclude(pk=self.instance.pk)
                lotes_camara = lotes_camara.exclude(pk=self.instance.pk)

                kg_procesados = (
                    self.instance.kilogramos_iniciales
                    - obtener_kilogramos_disponibles(self.instance)
                )

                if kg_iniciales < kg_procesados:
                    raise serializers.ValidationError({
                        "kilogramos_iniciales": (
                            "No puede ser menor que la cantidad ya procesada."
                        )
                    })
            else:
                kg_procesados = Decimal("0")

            asignado = lotes_captura.aggregate(
                total=Sum("kilogramos_iniciales")
            )["total"] or Decimal("0")

            if asignado + kg_iniciales > captura.kilogramos:
                raise serializers.ValidationError({
                    "kilogramos_iniciales": (
                        "La cantidad almacenada supera los kilogramos capturados."
                    )
                })

            ocupacion = sum(
                (
                    obtener_kilogramos_disponibles(lote)
                    for lote in lotes_camara
                ),
                Decimal("0"),
            )

            nueva_existencia = kg_iniciales - kg_procesados

            if ocupacion + nueva_existencia > camara.capacidad_kg:
                raise serializers.ValidationError({
                    "camara": (
                        "La cantidad supera la capacidad disponible de la cámara."
                    )
                })

        return data