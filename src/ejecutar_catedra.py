import ast
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from runpy import run_path
from tokenize import open as abrir_fuente
from urllib.parse import urlsplit

from controlador import Controlador, argumentos, ejecutar, leer_inventario


SCRIPTS = {
    "01": "01_get-ticket.py",
    "02": "02_get-network-device.py",
    "03": "03_get-host.py",
    "04": "04_tabulate.py",
}


class AdaptarOriginal(ast.NodeTransformer):
    def visit_Call(self, nodo):
        funcion = nodo.func
        if not (
            isinstance(funcion, ast.Attribute)
            and isinstance(funcion.value, ast.Name)
            and funcion.value.id == "requests"
        ):
            return self.generic_visit(nodo)
        if funcion.attr == "post":
            llamada = ast.Call(ast.Name("_autenticar", ast.Load()), [], [])
        elif funcion.attr == "get":
            llamada = ast.Call(ast.Name("_consultar", ast.Load()), [nodo.args[0]], [])
        else:
            return self.generic_visit(nodo)
        return ast.copy_location(llamada, nodo)

    def visit_Subscript(self, nodo):
        if (
            isinstance(nodo.value, ast.Name)
            and nodo.value.id in {"networkDevice", "host", "item"}
            and isinstance(nodo.slice, ast.Constant)
            and isinstance(nodo.slice.value, str)
            and isinstance(nodo.ctx, ast.Load)
        ):
            lectura = ast.Call(
                ast.Attribute(nodo.value, "get", ast.Load()),
                [nodo.slice, ast.Constant("No informado")],
                [],
            )
            return ast.copy_location(lectura, nodo)
        return self.generic_visit(nodo)


def ejecutar_original(ruta, controlador):
    def consultar(url):
        recurso = urlsplit(url).path.rsplit("/", 1)[-1]
        respuesta = controlador.consultar(recurso)
        leer_inventario(respuesta, recurso)
        return respuesta

    with abrir_fuente(ruta) as fuente:
        arbol = ast.parse(fuente.read(), filename=str(ruta))
    arbol = AdaptarOriginal().visit(arbol)
    codigo = compile(ast.fix_missing_locations(arbol), str(ruta), "exec")
    exec(codigo, {
        "__name__": "__main__",
        "__file__": str(ruta),
        "_autenticar": controlador.autenticar,
        "_consultar": consultar,
    })


def mostrar_salida(texto, controlador):
    for secreto in (controlador.clave, controlador.ticket):
        if secreto:
            texto = texto.replace(repr(secreto)[1:-1], "[oculto]")
            texto = texto.replace(secreto, "[oculto]")
    print(texto, end="")


def main():
    parser = argumentos("Ejecuta los originales y la auditoría contra la API de Packet Tracer.")
    parser.add_argument("script", choices=[*SCRIPTS, "todos"])
    args = parser.parse_args()
    controlador = Controlador(args.url, args.usuario)

    seleccion = SCRIPTS if args.script == "todos" else [args.script]
    with controlador.sesion:
        for numero in seleccion:
            nombre = SCRIPTS[numero]
            print(f"\n{nombre}")
            salida = StringIO()
            with redirect_stdout(salida):
                ejecutar_original(Path(__file__).with_name(nombre), controlador)
            if numero == "01":
                print("Ticket obtenido correctamente.")
                continue
            texto = salida.getvalue()
            if numero == "04":
                texto = texto.replace(f"\nEl Service Ticket es:\n{controlador.ticket}\n", "")
            mostrar_salida(texto, controlador)
        if args.script == "todos":
            nombre = "05_auditar_inventario.py"
            print(f"\n{nombre}")
            auditoria = run_path(str(Path(__file__).with_name(nombre)))
            salida = StringIO()
            with redirect_stdout(salida):
                auditoria["mostrar_auditoria"](controlador)
            mostrar_salida(salida.getvalue(), controlador)


if __name__ == "__main__":
    ejecutar(main)
