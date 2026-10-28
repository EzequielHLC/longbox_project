"""Acto 5 · Carga con sesiones reales de los tres roles (RNF-07, RNF-02).

    locust -f scripts/demo/locustfile.py --headless -u 50 -r 5 -t 10m
        --host https://127.0.0.1:8443 --csv scripts/demo/salida/carga_50

Cada usuario virtual inicia sesión con su propia cuenta (las de `poblar.py`,
contraseña `Demo-2026!`) y repite una mezcla realista de su rol, con una pausa
de 1 a 3 segundos entre pedidos:

- **Cliente** (60 %): catálogo, búsqueda, ficha, agregar al carrito y verlo.
- **Cajero** (25 %): búsqueda en el inventario y ficha de producto.
- **Administrador** (15 %): inventario, cola de correos, cuentas y auditoría.

Cada pedido lleva un nombre fijo, para que las estadísticas se agrupen por
operación y no por dirección. Cliente y servidor comparten la máquina: los
números miden el sistema más la herramienta.
"""

import itertools
import random
import re
import sys
from pathlib import Path

from locust import HttpUser, between, task

sys.path.insert(0, str(Path(__file__).resolve().parent))
from entorno import AUTORIDAD_LOCAL  # noqa: E402

CONTRASENA = "Demo-2026!"  # nosec B105 - cuentas de demostración
# Elige páginas y productos para simular la carga; no es criptografía.
azar = random.Random()  # nosec B311 - simula carga, no es criptografía
BUSQUEDAS = ["one", "dragon", "akira", "berserk", "noche", "figura", "fundas", "manga", "a", "z"]
_clientes = itertools.count(1)
_cajeros = itertools.count(1)
_administradores = itertools.count(1)


class Sesion(HttpUser):
    abstract = True
    wait_time = between(1, 3)
    correo = ""

    def on_start(self):
        self.client.verify = AUTORIDAD_LOCAL
        self.client.get("/cuentas/login/", name="inicio de sesión (GET)")
        token = self.client.cookies.get("csrftoken", "")
        self.client.post(
            "/cuentas/login/",
            {"username": self.correo, "password": CONTRASENA, "csrfmiddlewaretoken": token},
            headers={"Referer": f"{self.host}/cuentas/login/"},
            name="inicio de sesión (POST)",
        )
        self.productos = []

    def ids_de(self, html):
        return [int(x) for x in re.findall(r"/tienda/producto/(\d+)/", html)] or [
            int(x) for x in re.findall(r"/catalogo/productos/(\d+)/", html)
        ]


class Cliente(Sesion):
    weight = 60

    def on_start(self):
        self.correo = f"cliente{(next(_clientes) - 1) % 500 + 1:03d}@longbox.demo"
        super().on_start()

    @task(4)
    def catalogo(self):
        pagina = azar.randint(1, 20)
        respuesta = self.client.get(
            f"/tienda/catalogo/?estado=todos&page={pagina}", name="tienda: catálogo"
        )
        self.productos = self.ids_de(respuesta.text) or self.productos

    @task(3)
    def busqueda(self):
        respuesta = self.client.get(
            f"/tienda/catalogo/?q={azar.choice(BUSQUEDAS)}", name="tienda: búsqueda"
        )
        self.productos = self.ids_de(respuesta.text) or self.productos

    @task(3)
    def ficha(self):
        if self.productos:
            self.client.get(
                f"/tienda/producto/{azar.choice(self.productos)}/", name="tienda: ficha"
            )

    @task(1)
    def agregar_y_ver(self):
        if not self.productos:
            return
        token = self.client.cookies.get("csrftoken", "")
        self.client.post(
            f"/tienda/carrito/agregar/{azar.choice(self.productos)}/",
            {"cantidad": 1, "csrfmiddlewaretoken": token},
            headers={"Referer": f"{self.host}/tienda/catalogo/"},
            name="carrito: agregar",
        )
        self.client.get("/tienda/carrito/", name="carrito: ver")


class Cajero(Sesion):
    weight = 25

    def on_start(self):
        self.correo = f"cajero{(next(_cajeros) - 1) % 7 + 1}@longbox.demo"
        super().on_start()

    @task(3)
    def inventario(self):
        respuesta = self.client.get(
            f"/catalogo/productos/?q={azar.choice(BUSQUEDAS)}", name="inventario: búsqueda"
        )
        self.productos = self.ids_de(respuesta.text) or self.productos

    @task(2)
    def ficha(self):
        if self.productos:
            self.client.get(
                f"/catalogo/productos/{azar.choice(self.productos)}/", name="inventario: ficha"
            )


class Administrador(Sesion):
    weight = 15

    def on_start(self):
        self.correo = f"admin{(next(_administradores) - 1) % 3 + 1}@longbox.demo"
        super().on_start()

    @task(3)
    def inventario(self):
        respuesta = self.client.get(
            f"/catalogo/productos/?page={azar.randint(1, 50)}", name="inventario: página"
        )
        self.productos = self.ids_de(respuesta.text) or self.productos

    @task(2)
    def correos(self):
        self.client.get("/proveedores/correos/", name="correos: cola")

    @task(1)
    def cuentas(self):
        self.client.get("/cuentas/clientes/", name="cuentas: clientes")

    @task(1)
    def auditoria(self):
        self.client.get(f"/auditoria/?page={azar.randint(1, 100)}", name="auditoría: página")
