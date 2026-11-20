import argparse
from getpass import GetPassWarning, getpass
from urllib.parse import urlsplit
from warnings import catch_warnings, simplefilter

import requests


def argumentos(descripcion):
    parser = argparse.ArgumentParser(description=descripcion)
    parser.add_argument("--url", default="http://localhost:58000/api/v1")
    parser.add_argument("--usuario")
    return parser


def leer_inventario(respuesta, recurso):
    cuerpo = respuesta.json()
    if not isinstance(cuerpo, dict) or "response" not in cuerpo:
        raise ValueError(f"GET /{recurso} devolvió HTTP {respuesta.status_code} sin el campo response.")
    registros = cuerpo["response"]
    if not isinstance(registros, list):
        raise ValueError(
            f"GET /{recurso}: se esperaba una lista en response "
            f"y se recibió {type(registros).__name__}."
        )
    if any(not isinstance(registro, dict) for registro in registros):
        raise ValueError(f"GET /{recurso}: response contiene registros que no son objetos JSON.")
    return registros


class Controlador:
    def __init__(self, url, usuario):
        partes = urlsplit(url)
        if (
            partes.scheme not in ("http", "https")
            or not partes.hostname
            or partes.username is not None
            or partes.password is not None
            or partes.query
            or partes.fragment
        ):
            raise ValueError("Usá una URL HTTP(S) de la API sin credenciales.")
        self.url = url.rstrip("/")
        self.usuario = usuario or input("Usuario del controlador: ")
        with catch_warnings():
            simplefilter("error", GetPassWarning)
            try:
                self.clave = getpass("Clave del controlador: ")
            except GetPassWarning:
                raise ValueError("Usá una terminal interactiva para ingresar la clave sin eco.") from None
        self.sesion = requests.Session()
        self.ticket = None

    def solicitar(self, metodo, recurso, **opciones):
        respuesta = self.sesion.request(
            metodo, f"{self.url}/{recurso}", timeout=5,
            allow_redirects=False, **opciones
        )
        if not 200 <= respuesta.status_code < 300:
            raise ValueError(f"{metodo} /{recurso} devolvió HTTP {respuesta.status_code}.")
        return respuesta

    def autenticar(self):
        respuesta = self.solicitar(
            "POST", "ticket", json={"username": self.usuario, "password": self.clave}
        )
        self.ticket = respuesta.json()["response"]["serviceTicket"]
        if not isinstance(self.ticket, str) or not self.ticket:
            raise ValueError("El controlador no devolvió un ticket válido.")
        return respuesta

    def consultar(self, recurso):
        if self.ticket is None:
            self.autenticar()
        return self.solicitar("GET", recurso, headers={"X-Auth-Token": self.ticket})


def ejecutar(accion):
    try:
        accion()
    except requests.exceptions.JSONDecodeError:
        raise SystemExit("El controlador devolvió una respuesta que no es JSON.") from None
    except requests.RequestException:
        raise SystemExit("Falló la conexión con la API. Revisá la URL y el acceso en Packet Tracer.") from None
    except (KeyError, TypeError):
        raise SystemExit("La respuesta del controlador tiene un formato inesperado.") from None
    except ValueError as error:
        raise SystemExit(str(error)) from None
