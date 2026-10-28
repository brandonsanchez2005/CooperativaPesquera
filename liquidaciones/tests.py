from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from faenas.models import Captura, Embarcacion, Especie, Faena, Pescador
from .models import GastoFaena, Liquidacion


User = get_user_model()


class LiquidacionesApiTests(APITestCase):
    def setUp(self):
        grupo, _ = Group.objects.get_or_create(name="Operador")
        operador = User.objects.create_user(
            username="operador_liquidaciones",
            password="Clave-prueba-123",
        )
        operador.groups.add(grupo)

        token = Token.objects.create(user=operador)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        ahora = timezone.now()
        self.hoy = timezone.localdate()

        self.pescador = Pescador.objects.create(
            nombre="Pescador de liquidaciones",
            identificacion="LIQ-PESC-001",
            usuario=operador,
        )
        embarcacion = Embarcacion.objects.create(
            nombre="Lancha liquidaciones",
            matricula="LIQ-EMB-001",
            capacidad_kg=Decimal("100.00"),
        )
        especie = Especie.objects.create(
            nombre="Pargo liquidaciones",
            temperatura_maxima=Decimal("4.00"),
        )
        self.faena = Faena.objects.create(
            pescador=self.pescador,
            embarcacion=embarcacion,
            fecha_salida=ahora,
            fecha_regreso=ahora + timedelta(hours=8),
            zona="Puntarenas",
        )
        Captura.objects.create(
            faena=self.faena,
            especie=especie,
            kilogramos=Decimal("10.00"),
            precio_kg=Decimal("2500.00"),
        )

    def datos_gasto(self, monto="5000.00"):
        return {
            "faena": self.faena.id,
            "tipo": "HIELO",
            "descripcion": "Hielo financiado para la faena",
            "monto": monto,
            "fecha": self.hoy.isoformat(),
        }

    def test_crea_gasto_valido(self):
        respuesta = self.client.post(
            "/api/liquidaciones/gastos/",
            self.datos_gasto(),
            format="json",
        )

        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(
            Decimal(respuesta.data["monto"]),
            Decimal("5000.00"),
        )

    def test_rechaza_gasto_mayor_que_monto_bruto(self):
        respuesta = self.client.post(
            "/api/liquidaciones/gastos/",
            self.datos_gasto(monto="26000.00"),
            format="json",
        )

        self.assertEqual(respuesta.status_code, 400)

    def test_calcula_monto_bruto_gastos_y_neto(self):
        GastoFaena.objects.create(
            faena=self.faena,
            tipo="COMBUSTIBLE",
            descripcion="Combustible financiado",
            monto=Decimal("5000.00"),
            fecha=self.hoy,
        )

        respuesta = self.client.post(
            "/api/liquidaciones/",
            {
                "faena": self.faena.id,
                "fecha_liquidacion": self.hoy.isoformat(),
                "estado": "PENDIENTE",
            },
            format="json",
        )

        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(
            Decimal(respuesta.data["monto_bruto"]),
            Decimal("25000.00"),
        )
        self.assertEqual(
            Decimal(respuesta.data["total_gastos"]),
            Decimal("5000.00"),
        )
        self.assertEqual(
            Decimal(respuesta.data["monto_neto"]),
            Decimal("20000.00"),
        )

    def test_rechaza_liquidar_faena_sin_capturas(self):
        otra_faena = Faena.objects.create(
            pescador=self.pescador,
            embarcacion=self.faena.embarcacion,
            fecha_salida=timezone.now(),
            fecha_regreso=timezone.now() + timedelta(hours=6),
            zona="Quepos",
        )

        respuesta = self.client.post(
            "/api/liquidaciones/",
            {"faena": otra_faena.id},
            format="json",
        )

        self.assertEqual(respuesta.status_code, 400)

    def test_no_permite_gasto_despues_de_pagar_liquidacion(self):
        liquidacion = Liquidacion.objects.create(faena=self.faena)

        respuesta_pago = self.client.patch(
            f"/api/liquidaciones/{liquidacion.id}/",
            {"estado": "PAGADA"},
            format="json",
        )
        self.assertEqual(respuesta_pago.status_code, 200)

        respuesta_gasto = self.client.post(
            "/api/liquidaciones/gastos/",
            self.datos_gasto(monto="500.00"),
            format="json",
        )

        self.assertEqual(respuesta_gasto.status_code, 400)

    def test_no_permite_modificar_liquidacion_pagada(self):
        liquidacion = Liquidacion.objects.create(
            faena=self.faena,
            estado=Liquidacion.Estado.PAGADA,
        )

        respuesta = self.client.patch(
            f"/api/liquidaciones/{liquidacion.id}/",
            {"fecha_liquidacion": self.hoy.isoformat()},
            format="json",
        )

        self.assertEqual(respuesta.status_code, 400)

    def test_consulta_solo_ve_sus_liquidaciones(self):
        Liquidacion.objects.create(faena=self.faena)

        grupo, _ = Group.objects.get_or_create(name="Consulta")
        consulta = User.objects.create_user(
            username="consulta_liquidaciones",
            password="Clave-prueba-123",
        )
        consulta.groups.add(grupo)

        pescador_consulta = Pescador.objects.create(
            nombre="Pescadora de consulta",
            identificacion="LIQ-PESC-002",
            usuario=consulta,
        )
        faena_propia = Faena.objects.create(
            pescador=pescador_consulta,
            embarcacion=self.faena.embarcacion,
            fecha_salida=timezone.now(),
            fecha_regreso=timezone.now() + timedelta(hours=6),
            zona="Quepos",
        )
        Liquidacion.objects.create(faena=faena_propia)

        token = Token.objects.create(user=consulta)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        respuesta = self.client.get("/api/liquidaciones/")

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data["total_registros"], 1)
        self.assertEqual(
            respuesta.data["resultados"][0]["faena"],
            faena_propia.id,
        )

    def test_consulta_no_puede_crear_gasto(self):
        grupo, _ = Group.objects.get_or_create(name="Consulta")
        consulta = User.objects.create_user(
            username="consulta_gastos",
            password="Clave-prueba-123",
        )
        consulta.groups.add(grupo)
        token = Token.objects.create(user=consulta)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        respuesta = self.client.post(
            "/api/liquidaciones/gastos/",
            self.datos_gasto(),
            format="json",
        )

        self.assertEqual(respuesta.status_code, 403)

    def test_sin_token_recibe_401(self):
        self.client.credentials()

        respuesta = self.client.get("/api/liquidaciones/")

        self.assertEqual(respuesta.status_code, 401)