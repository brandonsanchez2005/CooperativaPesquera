from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase
from .models import Pescador, Embarcacion, Especie, Faena

User = get_user_model()


class FaenasApiTests(APITestCase):
    def setUp(self):
        grupo_operador, _ = Group.objects.get_or_create(name="Operador")
        self.operador = User.objects.create_user(
            username="operador", password="Clave-prueba-123"
        )

        self.operador.groups.add(grupo_operador)
        token = Token.objects.create(user=self.operador)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        self.pescador = Pescador.objects.create(
            nombre="Carlos Mora",
            identificacion="PESC-001",
            telefono="8000-0000",
            usuario=self.operador,
        )

        self.embarcacion = Embarcacion.objects.create(
            nombre="Mar Azul", matricula="P-001", capacidad_kg=100
        )

        self.especie = Especie.objects.create(nombre="Pargo", temperatura_maxima=4)
        self.faena = self.crear_faena()

    # ----------------------------------------------------------------------------------------

    def crear_faena(self, zona="Golfo de Nicoya"):
        return Faena.objects.create(
            pescador=self.pescador,
            embarcacion=self.embarcacion,
            fecha_salida="2026-10-25T06:00:00-06:00",
            fecha_regreso="2026-10-25T15:00:00-06:00",
            zona=zona,
        )

    def test_operador_crea_faena(self):
        respuesta = self.client.post(
            "/api/faenas/",
            {
                "pescador": self.pescador.id,
                "embarcacion": self.embarcacion.id,
                "fecha_salida": "2026-10-26T06:00:00-06:00",
                "fecha_regreso": "2026-10-26T15:00:00-06:00",
                "zona": "Quepos",
            },
            format="json",
        )

        self.assertEqual(respuesta.status_code, 201)

    # ----------------------------------------------------------------------------------------

    def test_lista_faenas(self):
        respuesta = self.client.get("/api/faenas/")
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data["total_registros"], 1)

    # ----------------------------------------------------------------------------------------

    def test_consulta_detalle_faena(self):
        respuesta = self.client.get(f"/api/faenas/{self.faena.id}/")
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data["zona"], "Golfo de Nicoya")

    # ----------------------------------------------------------------------------------------

    def test_actualiza_faena_con_patch(self):
        respuesta = self.client.patch(
            f"/api/faenas/{self.faena.id}/", {"zona": "Quepos"}, format="json"
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data["zona"], "Quepos")

    # ----------------------------------------------------------------------------------------

    def test_administrador_elimina_faena_sin_capturas(self):
        administrador = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="Clave-admin-123"
        )
        token = Token.objects.create(user=administrador)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        respuesta = self.client.delete(f"/api/faenas/{self.faena.id}/")
        self.assertEqual(respuesta.status_code, 204)

    # ----------------------------------------------------------------------------------------

    def test_fecha_regreso_anterior_es_error_400(self):
        respuesta = self.client.post(
            "/api/faenas/",
            {
                "pescador": self.pescador.id,
                "embarcacion": self.embarcacion.id,
                "fecha_salida": "2026-10-26T15:00:00-06:00",
                "fecha_regreso": "2026-10-26T06:00:00-06:00",
                "zona": "Quepos",
            },
            format="json",
        )
        self.assertEqual(respuesta.status_code, 400)

    # ----------------------------------------------------------------------------------------

    def test_captura_no_supera_capacidad_de_embarcacion(self):
        respuesta = self.client.post(
            "/api/capturas/",
            {
                "faena": self.faena.id,
                "especie": self.especie.id,
                "kilogramos": "101.00",
                "precio_kg": "2500.00",
            },
            format="json",
        )
        self.assertEqual(respuesta.status_code, 400)

    # ----------------------------------------------------------------------------------------

    def test_sin_token_recibe_401(self):
        self.client.credentials()
        respuesta = self.client.get("/api/faenas/")
        self.assertEqual(respuesta.status_code, 401)

    # ----------------------------------------------------------------------------------------

    def test_consulta_no_puede_crear_faena(self):
        grupo_consulta, _ = Group.objects.get_or_create(name="Consulta")
        consulta = User.objects.create_user(
            username="consulta", password="Clave-prueba-123"
        )
        consulta.groups.add(grupo_consulta)
        token = Token.objects.create(user=consulta)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        respuesta = self.client.post(
            "/api/faenas/",
            {
                "pescador": self.pescador.id,
                "embarcacion": self.embarcacion.id,
                "fecha_salida": "2026-10-26T06:00:00-06:00",
                "fecha_regreso": "2026-10-26T15:00:00-06:00",
                "zona": "Quepos",
            },
            format="json",
        )
        self.assertEqual(respuesta.status_code, 403)

    # ----------------------------------------------------------------------------------------

    def test_filtros_combinados_de_faena(self):

        self.crear_faena(zona="Quepos")

        respuesta = self.client.get(
            f"/api/faenas/?pescador={self.pescador.id}&zona=Nicoya"
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data["total_registros"], 1)

    # ----------------------------------------------------------------------------------------

    def test_consulta_solo_ve_sus_faenas(self):

        grupo_consulta, _ = Group.objects.get_or_create(name="Consulta")

        consulta = User.objects.create_user(
            username="pescadora", password="Clave-prueba-123"
        )
        consulta.groups.add(grupo_consulta)

        pescadora = Pescador.objects.create(
            nombre="Ana Solís", identificacion="PESC-002", usuario=consulta
        )

        faena_propia = Faena.objects.create(
            pescador=pescadora,
            embarcacion=self.embarcacion,
            fecha_salida="2026-10-25T06:00:00-06:00",
            fecha_regreso="2026-10-25T15:00:00-06:00",
            zona="Puntarenas",
        )

        token = Token.objects.create(user=consulta)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        respuesta = self.client.get("/api/faenas/")

        ids = [fila["id"] for fila in respuesta.data["resultados"]]

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(ids, [faena_propia.id])
