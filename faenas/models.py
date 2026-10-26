from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from decimal import Decimal

class Pescador(models.Model):

    nombre = models.CharField(max_length=100)
    identificacion = models.CharField(max_length=20, unique=True)
    telefono = models.CharField(max_length=20, blank=True)

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='perfil_pescador'
    )  
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

#------------------------------------------------------------------------
class Embarcacion(models.Model):

    nombre = models.CharField(max_length=100)
    matricula = models.CharField(max_length=30, unique=True)
    capacidad_kg = models.DecimalField(
    max_digits=9,
    decimal_places=2,
    validators=[MinValueValidator(Decimal('0.01'))]
    )
    activa = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.nombre} - {self.matricula}'

#--------------------------------------------------------------------------
class Especie(models.Model):

    nombre = models.CharField(max_length=80, unique=True)
    temperatura_maxima = models.DecimalField(
        max_digits=5,
        decimal_places=2
    )
    activa = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

#--------------------------------------------------------------------------
class Faena(models.Model):

    pescador = models.ForeignKey(
    Pescador,
        on_delete=models.PROTECT,
        related_name='faenas'
    )

    embarcacion = models.ForeignKey(
    Embarcacion,
        on_delete=models.PROTECT,
        related_name='faenas'
    )

    especies = models.ManyToManyField(
    Especie,
        through='Captura',
        related_name='faenas'
    )

    fecha_salida = models.DateTimeField()
    fecha_regreso = models.DateTimeField()
    zona = models.CharField(max_length=100)

    def __str__(self):
        return f'{self.pescador} - {self.fecha_salida:%Y-%m-%d}'

#---------------------------------------------------------------------------
class Captura(models.Model):

    faena = models.ForeignKey(
    Faena,
        on_delete=models.PROTECT,
        related_name='capturas'
    )

    especie = models.ForeignKey(
    Especie,
        on_delete=models.PROTECT,
        related_name='capturas'
    )

    kilogramos = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )

    precio_kg = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )

#----------------------------------------------------------------------------
class Meta:
    constraints = [
        models.UniqueConstraint(
            fields=['faena', 'especie'],
            name='especie_unica_por_faena'
        )
    ]
    def __str__(self):
        return f'{self.especie}: {self.kilogramos} kg'