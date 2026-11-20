from collections import defaultdict
from ipaddress import ip_address

from tabulate import tabulate

from controlador import Controlador, argumentos, ejecutar, leer_inventario


def auditar(dispositivos, hosts):
    direcciones = defaultdict(list)
    hallazgos = []
    for registros, tipo, nombre, campo_ip in (
        (dispositivos, "Dispositivo", "hostname", "managementIpAddress"),
        (hosts, "Host", "hostName", "hostIp"),
    ):
        for indice, registro in enumerate(registros, start=1):
            etiqueta = f"{tipo} {registro.get(nombre) or f'#{indice}'}"
            valor = registro.get(campo_ip)
            if not valor or (isinstance(valor, str) and not valor.strip()):
                hallazgos.append(("IP ausente", etiqueta))
                continue
            try:
                direccion = ip_address(str(valor).strip())
            except ValueError:
                hallazgos.append(("IP inválida", f"{etiqueta} ({valor})"))
                continue
            direcciones[direccion].append(etiqueta)
    for direccion, registros in direcciones.items():
        if len(registros) > 1:
            hallazgos.append(("IP repetida", f"{direccion} ({', '.join(registros)})"))
    return hallazgos


def mostrar_auditoria(controlador):
    dispositivos = leer_inventario(controlador.consultar("network-device"), "network-device")
    hosts = leer_inventario(controlador.consultar("host"), "host")
    hallazgos = auditar(dispositivos, hosts)
    print(f"Dispositivos: {len(dispositivos)} | Hosts: {len(hosts)}")
    if hallazgos:
        print(tabulate(hallazgos, headers=["Hallazgo", "Detalle"], tablefmt="simple"))
    else:
        print("Sin direcciones ausentes, inválidas o repetidas en los registros recibidos.")


def main():
    args = argumentos("Audita las direcciones IP del inventario del controlador.").parse_args()
    controlador = Controlador(args.url, args.usuario)
    with controlador.sesion:
        mostrar_auditoria(controlador)


if __name__ == "__main__":
    ejecutar(main)
