# Cooperativa Pesquera

API REST para gestionar pescadores, faenas, capturas, inventario, procesamiento, pedidos y liquidaciones de una cooperativa pesquera artesanal.

## Requisitos

- Python
- MySQL Server
- Una base de datos MySQL llamada `cooperativa_pesquera`

## Instalación y ejecución

Cree el entorno virtual e instale las dependencias:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Cree la base de datos en MySQL:

```sql
CREATE DATABASE cooperativa_pesquera CHARACTER SET utf8mb4;
```

Copie `.env.example` como `.env` y ajuste la clave secreta y los datos de conexión a MySQL. Para desarrollo local, agregue `DEBUG=True` al archivo `.env`.

```powershell
Copy-Item .env.example .env
```

Aplique las migraciones y cree un usuario administrador:

```powershell
python manage.py migrate
python manage.py createsuperuser
```

Inicie el servidor:

```powershell
python manage.py runserver
```

El panel administrativo está en `http://127.0.0.1:8000/admin/`.

## API y Postman

Obtenga un token con `POST http://127.0.0.1:8000/api/token/`, usando las credenciales de un usuario de Django. Envíe el token en las solicitudes protegidas con el encabezado:

```text
Authorization: Token <token>
```

Para probar la API, importe en Postman los archivos de `postman/` y seleccione el entorno **CooperativaPesquera Local**. Ingrese las credenciales solo en los valores locales del entorno.

## Pruebas

```powershell
python manage.py test
```

## Seguridad

No se sube `.env`, contraseñas ni tokens al repositorio. Use `.env.example` como plantilla.