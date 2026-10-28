from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from faenas.models import Captura, Embarcacion, Especie, Faena, Pescador
from inventario.models import CamaraFria, LoteInventario
from procesamiento.models import Procesamiento
from .models import Cliente, PrecioSemanal, Pedido


User = get_user_model()


class PedidosApiTests(APITestCase):
    def setUp(self):
        grupo, _ = Group.objects.get_or_create(name="Operador")
        operador = User.objects.create_user(
            username="operador_pedidos",
            password="Clave-prueba-123",
        )
        operador.groups.add(grupo)

        token = Token.objects.create(user=operador)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        hoy = timezone.localdate()
        ahora = timezone.now()

        self.cliente = Cliente.objects.create(
            nombre="Restaurante del Puerto",
            identificacion="PED-CLI-001",
            tipo=Cliente.TipoCliente.RESTAURANTE,
            correo="restaurante@example.com",
            telefono="8000-1000",
        )

        pescador = Pescador.objects.create(
            nombre="Pescador de prueba",
            identificacion="PED-PESC-001",
            usuario=operador,
        )
        embarcacion = Embarcacion.objects.create(
            nombre="Lancha de pedidos",
            matricula="PED-EMB-001",
            capacidad_kg=Decimal("100.00"),
        )
        self.especie = Especie.objects.create(
            nombre="Corvina pedidos",
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
            especie=self.especie,
            kilogramos=Decimal("40.00"),
            precio_kg=Decimal("2500.00"),
        )
        camara = CamaraFria.objects.create(
            codigo="PED-CAM-001",
            nombre="Cámara para pedidos",
            temperatura_actual=Decimal("2.00"),
            capacidad_kg=Decimal("100.00"),
        )
        lote = LoteInventario.objects.create(
            codigo="PED-LOTE-001",
            captura=captura,
            camara=camara,
            fecha_ingreso=hoy,
            fecha_vencimiento=hoy + timedelta(days=5),
            kilogramos_iniciales=Decimal("30.00"),
        )
        self.procesamiento = Procesamiento.objects.create(
            lote_inventario=lote,
            producto="FILETE",
            fecha_procesamiento=hoy,
            kilogramos_procesados=Decimal("12.00"),
            kilogramos_obtenidos=Decimal("8.00"),
            observaciones="Producto para pruebas",
        )

        self.precio = PrecioSemanal.objects.create(
            especie=self.especie,
            producto="FILETE",
            precio_kg=Decimal("5000.00"),
            vigente_desde=hoy - timedelta(days=1),
            vigente_hasta=hoy + timedelta(days=6),
        )

    def crear_pedido(self, fecha=None, estado=Pedido.Estado.PENDIENTE):
        return Pedido.objects.create(
            cliente=self.cliente,
            fecha_pedido=fecha or timezone.localdate(),
            estado=estado,
        )

    def test_crea_pedido(self):
        respuesta = self.client.post(
            "/api/pedidos/ordenes/",
            {
                "cliente": self.cliente.id,
                "fecha_pedido": timezone.localdate().isoformat(),
                "estado": "PENDIENTE",
            },
            format="json",
        )

        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(respuesta.data["estado"], "PENDIENTE")

    def test_rechaza_pedido_para_cliente_inactivo(self):
        cliente_inactivo = Cliente.objects.create(
            nombre="Cliente inactivo",
            identificacion="PED-CLI-002",
            tipo=Cliente.TipoCliente.HOTEL,
            activo=False,
        )

        respuesta = self.client.post(
            "/api/pedidos/ordenes/",
            {"cliente": cliente_inactivo.id},
            format="json",
        )

        self.assertEqual(respuesta.status_code, 400)

    def test_rechaza_precio_con_fechas_invertidas(self):
        respuesta = self.client.post(
            "/api/pedidos/precios/",
            {
                "especie": self.especie.id,
                "producto": "POSTA",
                "precio_kg": "4000.00",
                "vigente_desde": "2026-11-10",
                "vigente_hasta": "2026-11-01",
            },
            format="json",
        )

        self.assertEqual(respuesta.status_code, 400)

    def test_rechaza_periodo_de_precio_solapado(self):
        hoy = timezone.localdate()

        respuesta = self.client.post(
            "/api/pedidos/precios/",
            {
                "especie": self.especie.id,
                "producto": "FILETE",
                "precio_kg": "5200.00",
                "vigente_desde": (hoy + timedelta(days=2)).isoformat(),
                "vigente_hasta": (hoy + timedelta(days=8)).isoformat(),
            },
            format="json",
        )

        self.assertEqual(respuesta.status_code, 400)

    def test_crea_detalle_con_precio_semanal_vigente(self):
        pedido = self.crear_pedido()

        respuesta = self.client.post(
            "/api/pedidos/detalles/",
            {
                "pedido": pedido.id,
                "procesamiento": self.procesamiento.id,
                "kilogramos": "3.00",
            },
            format="json",
        )

        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(
            Decimal(respuesta.data["precio_kg"]),
            Decimal("5000.00"),
        )
        self.assertEqual(
            Decimal(respuesta.data["total_linea"]),
            Decimal("15000.00"),
        )

    def test_rechaza_detalle_si_no_hay_precio_vigente(self):
        pedido = self.crear_pedido(
            fecha=timezone.localdate() + timedelta(days=30)
        )

        respuesta = self.client.post(
            "/api/pedidos/detalles/",
            {
                "pedido": pedido.id,
                "procesamiento": self.procesamiento.id,
                "kilogramos": "2.00",
            },
            format="json",
        )

        self.assertEqual(respuesta.status_code, 400)

    def test_rechaza_vender_mas_kilogramos_de_los_obtenidos(self):
        pedido = self.crear_pedido()

        respuesta = self.client.post(
            "/api/pedidos/detalles/",
            {
                "pedido": pedido.id,
                "procesamiento": self.procesamiento.id,
                "kilogramos": "9.00",
            },
            format="json",
        )

        self.assertEqual(respuesta.status_code, 400)

    def test_rechaza_detalle_para_pedido_cancelado(self):
        pedido = self.crear_pedido(estado=Pedido.Estado.CANCELADO)

        respuesta = self.client.post(
            "/api/pedidos/detalles/",
            {
                "pedido": pedido.id,
                "procesamiento": self.procesamiento.id,
                "kilogramos": "2.00",
            },
            format="json",
        )

        self.assertEqual(respuesta.status_code, 400)

    def test_rechaza_entregar_pedido_sin_detalles(self):
        respuesta = self.client.post(
            "/api/pedidos/ordenes/",
            {
                "cliente": self.cliente.id,
                "fecha_pedido": timezone.localdate().isoformat(),
                "estado": "ENTREGADO",
            },
            format="json",
        )

        self.assertEqual(respuesta.status_code, 400)

    def test_consulta_no_puede_consultar_pedidos(self):
        grupo, _ = Group.objects.get_or_create(name="Consulta")
        consulta = User.objects.create_user(
            username="consulta_pedidos",
            password="Clave-prueba-123",
        )
        consulta.groups.add(grupo)
        token = Token.objects.create(user=consulta)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        respuesta = self.client.get("/api/pedidos/ordenes/")

        self.assertEqual(respuesta.status_code, 403)

    def test_sin_token_recibe_401(self):
        self.client.credentials()

        respuesta = self.client.get("/api/pedidos/ordenes/")

        self.assertEqual(respuesta.status_code, 401)