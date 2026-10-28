from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Cliente(models.Model):
    class TipoCliente(models.TextChoices):
        RESTAURANTE = "RESTAURANTE", "Restaurante"
        HOTEL = "HOTEL", "Hotel"
        PESCADERIA = "PESCADERIA", "Pescadería"
        OTRO = "OTRO", "Otro"

    nombre = models.CharField(max_length=100)
    identificacion = models.CharField(max_length=30, unique=True)
    tipo = models.CharField(max_length=20, choices=TipoCliente.choices)
    correo = models.EmailField(blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class PrecioSemanal(models.Model):
    class TipoProducto(models.TextChoices):
        FILETE = "FILETE", "Filete"
        POSTA = "POSTA", "Posta"
        ENTERO = "ENTERO", "Entero"
        OTRO = "OTRO", "Otro"

    especie = models.ForeignKey(
        "faenas.Especie",
        on_delete=models.PROTECT,
        related_name="precios_semanales",
    )
    producto = models.CharField(max_length=20, choices=TipoProducto.choices)
    precio_kg = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    vigente_desde = models.DateField()
    vigente_hasta = models.DateField()

    def __str__(self):
        return f"{self.especie} - {self.producto} - ₡{self.precio_kg}"


class Pedido(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        CONFIRMADO = "CONFIRMADO", "Confirmado"
        ENTREGADO = "ENTREGADO", "Entregado"
        CANCELADO = "CANCELADO", "Cancelado"

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name="pedidos",
    )
    fecha_pedido = models.DateField(default=timezone.localdate)
    estado = models.CharField(
        max_length=15,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
    )

    def __str__(self):
        return f"Pedido {self.id} - {self.cliente}"


class DetallePedido(models.Model):
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.PROTECT,
        related_name="detalles",
    )
    procesamiento = models.ForeignKey(
        "procesamiento.Procesamiento",
        on_delete=models.PROTECT,
        related_name="detalles_pedido",
    )
    kilogramos = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    precio_kg = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["pedido", "procesamiento"],
                name="procesamiento_unico_por_pedido",
            )
        ]

    def __str__(self):
        return f"Pedido {self.pedido_id}: {self.kilogramos} kg"