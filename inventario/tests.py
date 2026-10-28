from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from faenas.models import Captura, Embarcacion, Especie, Faena, Pescador
from .models import CamaraFria


User = get_user_model()


class InventarioApiTests(APITestCase):
    def setUp(self):
        grupo, _ = Group.objects.get_or_create(name="Operador")
        self.operador = User.objects.create_user(
            username="operador_inventario",
            password="Clave-prueba-123",
        )
        self.operador.groups.add(grupo)

        token = Token.objects.create(user=self.operador)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        ahora = timezone.now()
        pescador = Pescador.objects.create(
            nombre="Carlos Mora",
            identificacion="INV-PESC-001",
            usuario=self.operador,
        )
        embarcacion = Embarcacion.objects.create(
            nombre="Mar Azul",
            matricula="INV-EMB-001",
            capacidad_kg=Decimal("100.00"),
        )
        especie = Especie.objects.create(
            nombre="Pargo inventario",
            temperatura_maxima=Decimal("4.00"),
        )
        faena = Faena.objects.create(
            pescador=pescador,
            embarcacion=embarcacion,
            fecha_salida=ahora,
            fecha_regreso=ahora + timedelta(hours=8),
            zona="Puntarenas",
        )
        self.captura = Captura.objects.create(
            faena=faena,
            especie=especie,
            kilogramos=Decimal("60.00"),
            precio_kg=Decimal("2500.00"),
        )
        self.camara = CamaraFria.objects.create(
            codigo="INV-CAM-001",
            nombre="Cámara principal",
            temperatura_actual=Decimal("2.00"),
            capacidad_kg=Decimal("100.00"),
        )

    def datos_lote(self, codigo="INV-LOTE-001", kg="30.00", camara=None):
        return {
            "codigo": codigo,
            "captura": self.captura.id,
            "camara": (camara or self.camara).id,
            "fecha_ingreso": timezone.localdate().isoformat(),
            "fecha_vencimiento": (
                timezone.localdate() + timedelta(days=5)
            ).isoformat(),
            "kilogramos_iniciales": kg,
        }

    def test_crea_lote_valido(self):
        respuesta = self.client.post(
            "/api/inventario/lotes/",
            self.datos_lote(),
            format="json",
        )

        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(
            Decimal(respuesta.data["kilogramos_disponibles"]),
            Decimal("30.00"),
        )

    def test_rechaza_lote_mayor_que_captura(self):
        respuesta = self.client.post(
            "/api/inventario/lotes/",
            self.datos_lote(kg="61.00"),
            format="json",
        )

        self.assertEqual(respuesta.status_code, 400)

    def test_rechaza_camara_con_temperatura_inadecuada(self):
        camara_caliente = CamaraFria.objects.create(
            codigo="INV-CAM-002",
            nombre="Cámara caliente",
            temperatura_actual=Decimal("5.00"),
            capacidad_kg=Decimal("100.00"),
        )

        respuesta = self.client.post(
            "/api/inventario/lotes/",
            self.datos_lote(
                codigo="INV-LOTE-002",
                camara=camara_caliente,
            ),
            format="json",
        )

        self.assertEqual(respuesta.status_code, 400)

    def test_rechaza_exceso_de_capacidad_de_camara(self):
        self.camara.capacidad_kg = Decimal("40.00")
        self.camara.save(update_fields=["capacidad_kg"])

        primero = self.client.post(
            "/api/inventario/lotes/",
            self.datos_lote(codigo="INV-LOTE-003", kg="30.00"),
            format="json",
        )
        self.assertEqual(primero.status_code, 201)

        segundo = self.client.post(
            "/api/inventario/lotes/",
            self.datos_lote(codigo="INV-LOTE-004", kg="20.00"),
            format="json",
        )

        self.assertEqual(segundo.status_code, 400)

    def test_alerta_lote_proximo_a_vencer(self):
        datos = self.datos_lote(codigo="INV-LOTE-005")
        datos["fecha_vencimiento"] = (
            timezone.localdate() + timedelta(days=1)
        ).isoformat()

        creado = self.client.post(
            "/api/inventario/lotes/",
            datos,
            format="json",
        )
        self.assertEqual(creado.status_code, 201)

        respuesta = self.client.get("/api/inventario/alertas/")

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(len(respuesta.data), 1)

    def test_sin_token_recibe_401(self):
        self.client.credentials()

        respuesta = self.client.get("/api/inventario/camaras/")

        self.assertEqual(respuesta.status_code, 401)

    def test_consulta_no_puede_crear_camara(self):
        grupo, _ = Group.objects.get_or_create(name="Consulta")
        consulta = User.objects.create_user(
            username="consulta_inventario",
            password="Clave-prueba-123",
        )
        consulta.groups.add(grupo)
        token = Token.objects.create(user=consulta)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        respuesta = self.client.post(
            "/api/inventario/camaras/",
            {
                "codigo": "INV-CAM-003",
                "nombre": "Cámara de prueba",
                "temperatura_actual": "2.00",
                "capacidad_kg": "50.00",
                "activa": True,
            },
            format="json",
        )

        self.assertEqual(respuesta.status_code, 403)