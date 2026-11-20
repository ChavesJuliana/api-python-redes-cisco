# TP4 Integrador de Redes de Computadoras · UNLaM

Los scripts consultan el inventario del Cisco Network Controller de Packet Tracer. La topología del TP usa la IP `10.44.0.83`.

## 1. Preparar Python

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

## 3. Ejecutar los cuatro scripts de la cátedra y la auditoría

Desde la raíz del repositorio, ejecutá este comando en la terminal PowerShell de VS Code. El lanzador adapta en memoria las llamadas de los originales para usar la URL indicada y las credenciales ingresadas en la terminal. Las solicitudes HTTP se hacen al controlador. La clave se ingresa sin eco y el ticket se oculta en la salida.

```powershell
.\.venv\Scripts\python.exe .\src\ejecutar_catedra.py todos --url http://localhost:58000/api/v1
```

Para ejecutar un único script, reemplazá `todos` por su número. El lanzador obtiene un ticket automáticamente si la consulta requiere uno.

Si un registro omite un campo que los originales muestran, el lanzador lo presenta como «No informado». Si la respuesta de inventario tiene otra estructura, el error indica el endpoint y qué parte del formato falló.

| Número | Script | Resultado esperado |
| --- | --- | --- |
| 01 | `01_get-ticket.py` | Confirmación de que se obtuvo un ticket |
| 02 | `02_get-network-device.py` | Nombres, plataformas e IP de administración de los dispositivos |
| 03 | `03_get-host.py` | Nombres, IP, MAC e interfaces de conexión de los hosts |
| 04 | `04_tabulate.py` | Tablas de dispositivos y hosts |

## 4. Ejecutar solo el script propio

```powershell
.\.venv\Scripts\python.exe src/05_auditar_inventario.py --url $api
```

El script consulta `/network-device` y `/host` con un mismo ticket. Cuenta los registros y marca IP ausentes, inválidas o repetidas, incluso cuando la misma IP aparece en ambas listas. Una IP repetida es un hallazgo del inventario que se puede contrastar con la topología. El script solo solicita el ticket y consulta datos.

## 5. Registrar los resultados

| Comprobación | Resultado en este entorno |
| --- | --- |
| Conexión a `10.44.0.83:58000` | Tiempo de espera agotado |
| Conexión local a `127.0.0.1:58000` | Packet Tracer escucha en el puerto. La API devolvió HTTP 403 a una consulta de inventario sin ticket. |
| `01_get-ticket.py` | El controlador emitió un ticket con las credenciales ingresadas localmente. |
| `02_get-network-device.py` | HTTP 200. Se listaron 12 dispositivos. |
| `03_get-host.py` | HTTP 200. Se listaron 15 hosts. |
| `04_tabulate.py` | HTTP 201 al solicitar el ticket. Se mostraron las tablas con 12 dispositivos y 15 hosts. |
| `05_auditar_inventario.py` | Se auditaron 12 dispositivos y 15 hosts. No se encontraron IP ausentes, inválidas ni repetidas en los registros recibidos. |

Un dispositivo llegó sin los campos `hostname` y `softwareVersion`. El lanzador mostró «No informado» para esos campos y completó la ejecución. La auditoría revisó la IP de administración de cada dispositivo y la IP de cada host que devolvió el controlador. El README registra los resultados agregados de la corrida.
