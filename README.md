# TP4 Integrador de Redes de Computadoras · UNLaM

Los scripts consultan el inventario del Cisco Network Controller de Packet Tracer. La topología del TP usa la IP `10.44.0.83`.

## Estructura del repositorio

| Archivo | Finalidad |
| --- | --- |
| `README.md` | Describe la preparación, la ejecución y los resultados del TP. |
| `requirements.txt` | Fija las versiones de las dependencias de Python. |
| `.gitignore` | Excluye del repositorio los entornos virtuales, los archivos `.env` y la caché de Python. |
| `src/01_get-ticket.py` | Solicita un ticket de autenticación al controlador. |
| `src/02_get-network-device.py` | Lista los dispositivos de red con nombre, plataforma e IP de administración. |
| `src/03_get-host.py` | Lista los hosts con nombre, IP, MAC e interfaz de conexión. |
| `src/04_tabulate.py` | Presenta el inventario de dispositivos y hosts en tablas. |
| `src/05_auditar_inventario.py` | Script del grupo que detecta direcciones IP ausentes, inválidas o repetidas. |
| `src/controlador.py` | Centraliza la autenticación, las consultas HTTP y la validación de las respuestas de inventario. |

## 1. Preparar Python

La ejecución se verificó con Python 3.12. Los scripts usan `requests` para consultar la API y `tabulate` para mostrar tablas. Instalá ambas bibliotecas y sus dependencias desde `requirements.txt`.

En PowerShell, ejecutá estos comandos desde la raíz del repositorio.

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

En Linux, usá estos comandos.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

## 2. Confirmar el acceso a la API

Abrí la topología en Packet Tracer y habilitá **Enable External Access for Network Controller REST API** en **Preferences**. En el controlador, abrí **Config → Real World Access**, elegí el puerto en **HTTP Port** y marcá **Access Enabled**. Confirmá en **Server Status** que el servidor esté activo.

La IP `10.44.0.83` identifica al controlador dentro de la topología. Desde Windows, Packet Tracer expone la API en `localhost`. El ejemplo usa el puerto `58000` de los scripts originales. Si configuraste otro, cambialo en ambos comandos.

```powershell
Test-NetConnection localhost -Port 58000
$api = 'http://localhost:58000/api/v1'
```

Seguí con la autenticación cuando `TcpTestSucceeded` sea `True`. La configuración se describe en la ayuda integrada de Cisco Packet Tracer, en **Network Controllers → Real World Access**.

## 3. Ejecutar directamente los scripts de la cátedra

En PowerShell, desde la raíz del repositorio, prepará una copia local de los cuatro scripts dentro de `.venv`, que Git ignora. Guardá las credenciales y el ticket únicamente en esas copias.

```powershell
New-Item -ItemType Directory -Path .\.venv\scripts-tp4 -Force
Copy-Item .\src\01_get-ticket.py, .\src\02_get-network-device.py, .\src\03_get-host.py, .\src\04_tabulate.py -Destination .\.venv\scripts-tp4
```

Configurá el usuario y la clave del controlador en las copias de `01_get-ticket.py` y `04_tabulate.py`. Si usás un puerto distinto de `58000`, actualizalo en las cuatro copias.

```powershell
.\.venv\Scripts\python.exe .\.venv\scripts-tp4\01_get-ticket.py
```

Copiá el ticket que devuelve `01_get-ticket.py` en el encabezado `X-Auth-Token` de las copias de `02_get-network-device.py` y `03_get-host.py`. El `04_tabulate.py` solicita su propio ticket.

```powershell
.\.venv\Scripts\python.exe .\.venv\scripts-tp4\02_get-network-device.py
.\.venv\Scripts\python.exe .\.venv\scripts-tp4\03_get-host.py
.\.venv\Scripts\python.exe .\.venv\scripts-tp4\04_tabulate.py
```

| Script | Salida esperada |
| --- | --- |
| `01_get-ticket.py` | `Ticket request status: 201`, la respuesta de la API y el ticket. |
| `02_get-network-device.py` | `Request status: 200`, la respuesta de la API y una fila por dispositivo con nombre, plataforma e IP de administración. |
| `03_get-host.py` | `Request status: 200`, la respuesta de la API y una fila por host con nombre, IP, MAC e interfaz de conexión. |
| `04_tabulate.py` | Estado `201` al solicitar el ticket, seguido del ticket y las tablas **Dispositivos de Red** y **Hosts de la Red**. |

El `02` puede devolver HTTP 200 y luego terminar con `KeyError: 'hostname'` si un dispositivo viene sin ese campo. El `04` también necesita los campos que usa para construir sus tablas. Si compartís capturas de los scripts `01` o `04`, ocultá el valor del ticket donde aparezca.

## 4. Ejecutar solo el script propio

```powershell
.\.venv\Scripts\python.exe src/05_auditar_inventario.py --url $api
```

El script consulta `/network-device` y `/host` con un mismo ticket. Cuenta los registros y marca IP ausentes, inválidas o repetidas, incluso cuando la misma IP aparece en ambas listas. Una IP repetida es un hallazgo del inventario que se puede contrastar con la topología. El script solo solicita el ticket y consulta datos.

## 5. Resultados de la auditoría

| Comprobación | Resultado en este entorno |
| --- | --- |
| Conexión a `10.44.0.83:58000` | Tiempo de espera agotado |
| Conexión local a `127.0.0.1:58000` | Packet Tracer escucha en el puerto. La API devolvió HTTP 403 a una consulta de inventario sin ticket. |
| `05_auditar_inventario.py` | Se auditaron 12 dispositivos y 15 hosts. No se encontraron IP ausentes, inválidas ni repetidas en los registros recibidos. |
