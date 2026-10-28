from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from faenas.models import Captura, Embarcacion, Especie, Faena, Pescador
from inventario.models import CamaraFria, LoteInventario


User = get_user_model()


class ProcesamientoApiTests(APITestCase):
    def setUp(self):
        grupo, _ = Group.objects.get_or_create(name="Operador")
        self.operador = User.objects.create_user(
            username="operador_procesamiento",
            password="Clave-prueba-123",
        )
        self.operador.groups.add(grupo)

        token = Token.objects.create(user=self.operador)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        ahora = timezone.now()
        hoy = timezone.localdate()

        pescador = Pescador.objects.create(
            nombre="Ana Solís",
            identificacion="PROC-PESC-001",
            usuario=self.operador,
        )
        embarcacion = Embarcacion.objects.create(
            nombre="Barco procesamiento",
            matricula="PROC-EMB-001",
            capacidad_kg=Decimal("100.00"),
        )
        especie = Especie.objects.create(
            nombre="Corvina procesamiento",
            temperatura_maxima=Decimal("4.00"),
        )
        faena = Faena.objects.create(
            pescador=pescador,
            embarcacion=embarcacion,
            fecha_salida=ahora,
            fecha_regreso=ahora + timedelta(hours=8),
            zona="Quepos",
        )
        captura = Captura.objects.create(
            faena=faena,
            especie=especie,
            kilogramos=Decimal("60.00"),
            precio_kg=Decimal("3000.00"),
        )
        camara = CamaraFria.objects.create(
            codigo="PROC-CAM-001",
            nombre="Cámara procesamiento",
            temperatura_actual=Decimal("2.00"),
            capacidad_kg=Decimal("100.00"),
        )
        self.lote = LoteInventario.objects.create(
            codigo="PROC-LOTE-001",
            captura=captura,
            camara=camara,
            fecha_ingreso=hoy,
            fecha_vencimiento=hoy + timedelta(days=5),
            kilogramos_iniciales=Decimal("50.00"),
        )

    def datos_procesamiento(
        self,
        kg_procesados="10.00",
        kg_obtenidos="8.00",
    ):
        return {
            "lote_inventario": self.lote.id,
            "producto": "FILETE",
            "fecha_procesamiento": timezone.localdate().isoformat(),
            "kilogramos_procesados": kg_procesados,
            "kilogramos_obtenidos": kg_obtenidos,
            "observaciones": "Prueba de fileteo",
        }

    def test_merma_y_existencia_disponible(self):
        respuesta = self.client.post(
            "/api/procesamiento/",
            self.datos_procesamiento(),
            format="json",
        )

        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(
            Decimal(respuesta.data["merma_kg"]),
            Decimal("2.00"),
        )

        existencia = self.client.get(
            f"/api/inventario/lotes/{self.lote.id}/"
        )

        self.assertEqual(existencia.status_code, 200)
        self.assertEqual(
            Decimal(existencia.data["kilogramos_disponibles"]),
            Decimal("40.00"),
        )

    def test_rechaza_procesar_mas_de_lo_disponible(self):
        respuesta = self.client.post(
            "/api/procesamiento/",
            self.datos_procesamiento(
                kg_procesados="51.00",
                kg_obtenidos="40.00",
            ),
            format="json",
        )

        self.assertEqual(respuesta.status_code, 400)

    def test_rechaza_producto_obtenido_mayor_que_entrada(self):
        respuesta = self.client.post(
            "/api/procesamiento/",
            self.datos_procesamiento(
                kg_procesados="5.00",
                kg_obtenidos="6.00",
            ),
            format="json",
        )

        self.assertEqual(respuesta.status_code, 400)

    def test_rechaza_procesar_mas_que_la_existencia_restante(self):
        primero = self.client.post(
            "/api/procesamiento/",
            self.datos_procesamiento(
                kg_procesados="40.00",
                kg_obtenidos="32.00",
            ),
            format="json",
        )
        self.assertEqual(primero.status_code, 201)

        segundo = self.client.post(
            "/api/procesamiento/",
            self.datos_procesamiento(
                kg_procesados="11.00",
                kg_obtenidos="8.00",
            ),
            format="json",
        )

        self.assertEqual(segundo.status_code, 400)

    def test_patch_no_permite_producto_mayor_que_entrada(self):
        creado = self.client.post(
            "/api/procesamiento/",
            self.datos_procesamiento(),
            format="json",
        )
        self.assertEqual(creado.status_code, 201)

        respuesta = self.client.patch(
            f"/api/procesamiento/{creado.data['id']}/",
            {"kilogramos_obtenidos": "11.00"},
            format="json",
        )

        self.assertEqual(respuesta.status_code, 400)

    def test_sin_token_recibe_401(self):
        self.client.credentials()

        respuesta = self.client.get("/api/procesamiento/")

        self.assertEqual(respuesta.status_code, 401)

    def test_consulta_no_puede_crear_procesamiento(self):
        grupo, _ = Group.objects.get_or_create(name="Consulta")
        consulta = User.objects.create_user(
            username="consulta_procesamiento",
            password="Clave-prueba-123",
        )
        consulta.groups.add(grupo)
        token = Token.objects.create(user=consulta)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        respuesta = self.client.post(
            "/api/procesamiento/",
            self.datos_procesamiento(),
            format="json",
        )

        self.assertEqual(respuesta.status_code, 403)