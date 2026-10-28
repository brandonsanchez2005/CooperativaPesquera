from decimal import Decimal

from rest_framework import serializers

from inventario.serializers import obtener_kilogramos_disponibles
from .models import Procesamiento


class ProcesamientoSerializer(serializers.ModelSerializer):
    merma_kg = serializers.SerializerMethodField()

    class Meta:
        model = Procesamiento
        fields = (
            "id",
            "lote_inventario",
            "producto",
            "fecha_procesamiento",
            "kilogramos_procesados",
            "kilogramos_obtenidos",
            "merma_kg",
            "observaciones",
        )
        read_only_fields = ("merma_kg",)

    def get_merma_kg(self, obj):
        return obj.kilogramos_procesados - obj.kilogramos_obtenidos

    def validate(self, data):
        lote = data.get(
            "lote_inventario",
            getattr(self.instance, "lote_inventario", None),
        )
        fecha = data.get(
            "fecha_procesamiento",
            getattr(self.instance, "fecha_procesamiento", None),
        )
        kg_procesados = data.get(
            "kilogramos_procesados",
            getattr(self.instance, "kilogramos_procesados", None),
        )
        kg_obtenidos = data.get(
            "kilogramos_obtenidos",
            getattr(self.instance, "kilogramos_obtenidos", None),
        )

        if kg_procesados is None or kg_procesados <= Decimal("0"):
            raise serializers.ValidationError({
                "kilogramos_procesados": "Debe ser mayor que cero."
            })

        if kg_obtenidos is None or kg_obtenidos <= Decimal("0"):
            raise serializers.ValidationError({
                "kilogramos_obtenidos": "Debe ser mayor que cero."
            })

        if kg_obtenidos > kg_procesados:
            raise serializers.ValidationError({
                "kilogramos_obtenidos": (
                    "El producto obtenido no puede superar los kilogramos procesados."
                )
            })

        if lote and fecha:
            if fecha < lote.fecha_ingreso:
                raise serializers.ValidationError({
                    "fecha_procesamiento": (
                        "No puede preceder al ingreso del lote."
                    )
                })

            if fecha > lote.fecha_vencimiento:
                raise serializers.ValidationError({
                    "fecha_procesamiento": (
                        "No se puede procesar un lote vencido."
                    )
                })

            disponibles = obtener_kilogramos_disponibles(lote)

            if self.instance and self.instance.lote_inventario_id == lote.id:
                disponibles += self.instance.kilogramos_procesados

            if kg_procesados > disponibles:
                raise serializers.ValidationError({
                    "kilogramos_procesados": (
                        "La cantidad supera los kilogramos disponibles del lote."
                    )
                })

        return data