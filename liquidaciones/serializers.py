from decimal import Decimal

from rest_framework import serializers

from .models import GastoFaena, Liquidacion


def obtener_monto_bruto(faena):
    return sum(
        (
            captura.kilogramos * captura.precio_kg
            for captura in faena.capturas.all()
        ),
        Decimal("0"),
    )


def obtener_total_gastos(faena):
    return sum(
        (gasto.monto for gasto in faena.gastos.all()),
        Decimal("0"),
    )


class GastoFaenaSerializer(serializers.ModelSerializer):
    class Meta:
        model = GastoFaena
        fields = "__all__"

    def validate(self, data):
        faena = data.get(
            "faena", getattr(self.instance, "faena", None)
        )
        monto = data.get(
            "monto", getattr(self.instance, "monto", None)
        )

        if monto is None or monto <= Decimal("0"):
            raise serializers.ValidationError({
                "monto": "El monto debe ser mayor que cero."
            })

        if faena:
            if not faena.capturas.exists():
                raise serializers.ValidationError({
                    "faena": "La faena debe tener capturas para registrar gastos."
                })

            faenas_revisar = [faena]
            if self.instance:
                faenas_revisar.append(self.instance.faena)

            for faena_revisar in faenas_revisar:
                try:
                    liquidacion = faena_revisar.liquidacion
                except Liquidacion.DoesNotExist:
                    liquidacion = None

                if liquidacion and liquidacion.estado == Liquidacion.Estado.PAGADA:
                    raise serializers.ValidationError({
                        "faena": (
                            "No se pueden cambiar gastos de una liquidación pagada."
                        )
                    })

            gastos = GastoFaena.objects.filter(faena=faena)
            if self.instance and self.instance.faena_id == faena.id:
                gastos = gastos.exclude(pk=self.instance.pk)

            monto_existente = sum(
                (gasto.monto for gasto in gastos),
                Decimal("0"),
            )
            monto_bruto = obtener_monto_bruto(faena)

            if monto_existente + monto > monto_bruto:
                raise serializers.ValidationError({
                    "monto": (
                        "Los gastos no pueden superar el monto bruto de la faena."
                    )
                })

        return data


class LiquidacionSerializer(serializers.ModelSerializer):
    monto_bruto = serializers.SerializerMethodField()
    total_gastos = serializers.SerializerMethodField()
    monto_neto = serializers.SerializerMethodField()

    class Meta:
        model = Liquidacion
        fields = (
            "id",
            "faena",
            "fecha_liquidacion",
            "estado",
            "monto_bruto",
            "total_gastos",
            "monto_neto",
        )
        read_only_fields = ("monto_bruto", "total_gastos", "monto_neto")

    def get_monto_bruto(self, obj):
        return obtener_monto_bruto(obj.faena)

    def get_total_gastos(self, obj):
        return obtener_total_gastos(obj.faena)

    def get_monto_neto(self, obj):
        return obtener_monto_bruto(obj.faena) - obtener_total_gastos(obj.faena)

    def validate(self, data):
        faena = data.get(
            "faena", getattr(self.instance, "faena", None)
        )

        if self.instance and self.instance.estado == Liquidacion.Estado.PAGADA:
            raise serializers.ValidationError(
                "No se puede modificar una liquidación pagada."
            )

        if faena:
            if not faena.capturas.exists():
                raise serializers.ValidationError({
                    "faena": "La faena debe tener capturas para liquidarse."
                })

            monto_bruto = obtener_monto_bruto(faena)
            total_gastos = obtener_total_gastos(faena)

            if total_gastos > monto_bruto:
                raise serializers.ValidationError({
                    "faena": "Los gastos superan el monto bruto de la faena."
                })

        return data