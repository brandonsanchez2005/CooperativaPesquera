from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Procesamiento(models.Model):
    class TipoProducto(models.TextChoices):
        FILETE = "FILETE", "Filete"
        POSTA = "POSTA", "Posta"
        ENTERO = "ENTERO", "Entero"
        OTRO = "OTRO", "Otro"

    lote_inventario = models.ForeignKey(
        "inventario.LoteInventario",
        on_delete=models.PROTECT,
        related_name="procesamientos",
    )
    producto = models.CharField(
        max_length=20,
        choices=TipoProducto.choices,
    )
    fecha_procesamiento = models.DateField(default=timezone.localdate)
    kilogramos_procesados = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )
    kilogramos_obtenidos = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )
    observaciones = models.TextField(blank=True)

    def __str__(self):
        return f"{self.get_producto_display()} - {self.fecha_procesamiento}"