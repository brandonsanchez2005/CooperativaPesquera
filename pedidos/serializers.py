from decimal import Decimal

from django.db.models import Sum
from rest_framework import serializers

from procesamiento.models import Procesamiento
from .models import Cliente, PrecioSemanal, Pedido, DetallePedido

class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = "__all__"

class PrecioSemanalSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrecioSemanal
        fields = "__all__"

    def validate(self, data):
        especie = data.get(
            "especie", getattr(self.instance, "especie", None)
        )
        producto = data.get(
            "producto", getattr(self.instance, "producto", None)
        )
        desde = data.get(
            "vigente_desde", getattr(self.instance, "vigente_desde", None)
        )
        hasta = data.get(
            "vigente_hasta", getattr(self.instance, "vigente_hasta", None)
        )
        precio = data.get(
            "precio_kg", getattr(self.instance, "precio_kg", None)
        )

        if precio is not None and precio <= Decimal("0"):
            raise serializers.ValidationError({
                "precio_kg": "El precio debe ser mayor que cero."
            })

        if desde and hasta and hasta < desde:
            raise serializers.ValidationError({
                "vigente_hasta": "No puede preceder a la fecha inicial."
            })

        if especie and producto and desde and hasta:
            precios = PrecioSemanal.objects.filter(
                especie=especie,
                producto=producto,
                vigente_desde__lte=hasta,
                vigente_hasta__gte=desde,
            )

            if self.instance:
                precios = precios.exclude(pk=self.instance.pk)

            if precios.exists():
                raise serializers.ValidationError({
                    "vigente_desde": (
                        "Ya existe un precio para ese producto en ese periodo."
                    )
                })

        return data

class PedidoSerializer(serializers.ModelSerializer):
    total = serializers.SerializerMethodField()

    class Meta:
        model = Pedido
        fields = ("id", "cliente", "fecha_pedido", "estado", "total")
        read_only_fields = ("total",)

    def get_total(self, obj):
        return sum(
            (
                detalle.kilogramos * detalle.precio_kg
                for detalle in obj.detalles.all()
            ),
            Decimal("0"),
        )

    def validate(self, data):
        cliente = data.get(
            "cliente", getattr(self.instance, "cliente", None)
        )
        fecha = data.get(
            "fecha_pedido", getattr(self.instance, "fecha_pedido", None)
        )
        estado = data.get(
            "estado",
            getattr(self.instance, "estado", Pedido.Estado.PENDIENTE),
        )

        if cliente and not cliente.activo:
            raise serializers.ValidationError({
                "cliente": "No se pueden crear pedidos para un cliente inactivo."
            })

        if self.instance:
            if (
                self.instance.estado == Pedido.Estado.CANCELADO
                and estado != Pedido.Estado.CANCELADO
            ):
                raise serializers.ValidationError({
                    "estado": "Un pedido cancelado no se puede reactivar."
                })

            if (
                self.instance.detalles.exists()
                and fecha != self.instance.fecha_pedido
            ):
                raise serializers.ValidationError({
                    "fecha_pedido": (
                        "No se puede cambiar la fecha de un pedido con detalles."
                    )
                })

        if estado == Pedido.Estado.ENTREGADO:
            if not self.instance or not self.instance.detalles.exists():
                raise serializers.ValidationError({
                    "estado": "No se puede entregar un pedido sin detalles."
                })

        return data

class DetallePedidoSerializer(serializers.ModelSerializer):
    total_linea = serializers.SerializerMethodField()

    class Meta:
        model = DetallePedido
        fields = (
            "id",
            "pedido",
            "procesamiento",
            "kilogramos",
            "precio_kg",
            "total_linea",
        )
        read_only_fields = ("precio_kg", "total_linea")

    def get_total_linea(self, obj):
        return obj.kilogramos * obj.precio_kg

    def validate(self, data):
        pedido = data.get(
            "pedido", getattr(self.instance, "pedido", None)
        )
        procesamiento = data.get(
            "procesamiento",
            getattr(self.instance, "procesamiento", None),
        )
        kg = data.get(
            "kilogramos", getattr(self.instance, "kilogramos", None)
        )

        if pedido and pedido.estado in [
            Pedido.Estado.CANCELADO,
            Pedido.Estado.ENTREGADO,
        ]:
            raise serializers.ValidationError({
                "pedido": "No se pueden cambiar los detalles de este pedido."
            })

        if kg is None or kg <= Decimal("0"):
            raise serializers.ValidationError({
                "kilogramos": "La cantidad debe ser mayor que cero."
            })

        if pedido and procesamiento:
            especie = procesamiento.lote_inventario.captura.especie

            precios = PrecioSemanal.objects.filter(
                especie=especie,
                producto=procesamiento.producto,
                vigente_desde__lte=pedido.fecha_pedido,
                vigente_hasta__gte=pedido.fecha_pedido,
            ).order_by("-vigente_desde")

            precio = precios.first()

            if precio is None:
                raise serializers.ValidationError({
                    "procesamiento": (
                        "No hay precio vigente para ese producto en la fecha del pedido."
                    )
                })

            reservados = DetallePedido.objects.filter(
                procesamiento=procesamiento
            ).exclude(pedido__estado=Pedido.Estado.CANCELADO)

            if self.instance:
                reservados = reservados.exclude(pk=self.instance.pk)

            kg_reservados = reservados.aggregate(
                total=Sum("kilogramos")
            )["total"] or Decimal("0")

            disponibles = procesamiento.kilogramos_obtenidos - kg_reservados

            if kg > disponibles:
                raise serializers.ValidationError({
                    "kilogramos": (
                        "La cantidad supera el producto disponible para venta."
                    )
                })

            data["precio_kg"] = precio.precio_kg

        return data