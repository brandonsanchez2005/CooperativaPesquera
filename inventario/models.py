from django.db import models


class CamaraFria(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100)
    temperatura_actual = models.DecimalField(max_digits=5, decimal_places=2)
    capacidad_kg = models.DecimalField(max_digits=9, decimal_places=2)
    activa = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"


class LoteInventario(models.Model):
    codigo = models.CharField(max_length=30, unique=True)
    captura = models.ForeignKey(
        "faenas.Captura",
        on_delete=models.PROTECT,
        related_name="lotes_inventario",
    )
    camara = models.ForeignKey(
        CamaraFria,
        on_delete=models.PROTECT,
        related_name="lotes",
    )
    fecha_ingreso = models.DateField()
    fecha_vencimiento = models.DateField()
    kilogramos_iniciales = models.DecimalField(
        max_digits=9,
        decimal_places=2,
    )

    def __str__(self):
        return self.codigo