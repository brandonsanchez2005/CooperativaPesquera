from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

class GastoFaena(models.Model):
    class TipoGasto(models.TextChoices):
        HIELO = "HIELO", "Hielo"
        COMBUSTIBLE = "COMBUSTIBLE", "Combustible"
        OTRO = "OTRO", "Otro"

    faena = models.ForeignKey(
        "faenas.Faena",
        on_delete=models.PROTECT,
        related_name="gastos",
    )
    tipo = models.CharField(max_length=20, choices=TipoGasto.choices)
    descripcion = models.CharField(max_length=150)
    monto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    fecha = models.DateField(default=timezone.localdate)

    def __str__(self):
        return f"{self.get_tipo_display()} - ₡{self.monto}"

class Liquidacion(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        PAGADA = "PAGADA", "Pagada"

    faena = models.OneToOneField(
        "faenas.Faena",
        on_delete=models.PROTECT,
        related_name="liquidacion",
    )
    fecha_liquidacion = models.DateField(default=timezone.localdate)
    estado = models.CharField(
        max_length=12,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
    )

    def __str__(self):
        return f"Liquidación de faena {self.faena_id}"