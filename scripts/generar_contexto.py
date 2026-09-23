#!/usr/bin/env python3
"""
Genera `.contexto-ia/` desde el documento de análisis.

    python scripts/generar_contexto.py

Parte el documento en archivos chicos para que no haya que leerlo entero. Es un volcado, no una
interpretación: lo que queda en `.contexto-ia/` dice lo mismo que el documento.

Qué escribe y qué NO toca
-------------------------
Escribe, y por lo tanto pisa en cada corrida:

    .contexto-ia/INDICE.md          los casos de uso con su módulo y su archivo
    .contexto-ia/CONTEXTO.md        contexto, escenario, objetivos
    .contexto-ia/ALCANCE.md         alcance, límites, suposiciones
    .contexto-ia/REQUISITOS.md      RF, RNF y reglas del dominio
    .contexto-ia/ACTORES.md         actores y procesos automatizados
    .contexto-ia/cu/NN-modulo.md    fichas extendidas
    .contexto-ia/contratos/*.md     contratos de operación

**Nunca toca los archivos que mantiene el responsable a mano**, aunque estén en la misma carpeta:

    .contexto-ia/MODELO_DE_DOMINIO.md         requiere análisis, no extracción
    .contexto-ia/dss/                         los diagramas de secuencia del sistema
    .contexto-ia/dss/inventario_operaciones.md
    .contexto-ia/tokens_visuales.md
    .contexto-ia/ESTRUCTURA.md                lo genera otro script
    .contexto-ia/identidad_visual.md          material personal
    .contexto-ia/referencias-pantallas/       idem

Esa lista no es una cortesía: es la condición para que el responsable pueda mantener material a
mano en la misma carpeta. Por eso no alcanza con no escribirlos, y el script **verifica al
terminar** que ninguno haya desaparecido ni cambiado durante la corrida. Si alguno cambió, sale
con error: una corrida que se lleva puestas horas de análisis no debe poder pasar en silencio.

El modelo de dominio no se genera. Requiere análisis, no extracción: decidir qué es concepto y
qué es atributo, qué asociación existe y con qué multiplicidad. Un script no puede hacerlo, y
fingir que sí produciría un archivo plausible y equivocado.

El capítulo "Estado de Construcción" del documento tampoco se extrae, a propósito. La autoridad
del estado es `docs/ESTADO.md`; ese capítulo se escribe *desde* ahí cuando se arma el documento.
Extraerlo crearía un segundo domicilio del mismo hecho y los dos divergirían.

Dónde se archiva cada contrato
------------------------------
**Por sus Referencias Cruzadas, no por su posición en el documento.** Cada contrato declara a qué
casos de uso pertenece; de ahí sale el módulo, y de ahí el archivo.

Archivar por posición fue el error que se coló en la corrida del 2026-09-14: 64 contratos de todos
los módulos quedaron bajo el 18, porque en el documento vienen después del último encabezado
numerado. Los encabezados de capítulo que sí existen —«Transversales», «Contratos de Operaciones
de Solo Lectura»— no llevan número de módulo, así que no abren módulo nuevo y el que estaba
abierto se los quedó a todos.

Un contrato cuyos casos de uso viven en más de un módulo no pertenece a ninguno: va a
`contratos/00-transversales.md`. Es el caso de `CO-156 cancelarOperacion`, referenciado por quince
casos de uso de ocho módulos.

Verificación
------------
El script no falla en silencio. Al terminar informa qué esperaba encontrar y no encontró:

1. Fichas sin contrato, contratos sin ficha, casos de uso sin flujo, módulos vacíos.
2. Huecos en la numeración de contratos.
3. **Contratos archivados donde ninguno de sus casos de uso vive.** Es el chequeo que faltaba el
   2026-09-14 y el que habría detectado el problema de arriba: la numeración corría sin saltos,
   así que ningún otro chequeo lo veía.
4. **Consistencia por nombre de operación entre tres fuentes**: los contratos volcados, el
   inventario de operaciones y los DSS. Una operación se vincula con su contrato **por el nombre**
   y nunca por un número de operación: el inventario numera `OP-nnn` y afirma que a cada uno le
   corresponde un `C-nnn` con el mismo número, y esa correspondencia hay que comprobarla, no
   suponerla.
5. Que los archivos del responsable sigan como estaban.

**El chequeo informa y no corrige.** Las diferencias van a `docs/DEUDA.md`, que es donde vive la
distancia entre lo especificado y lo construido. Un generador que ajusta lo que encuentra deja de
ser un volcado y pasa a ser una interpretación.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
import unicodedata
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

# --------------------------------------------------------------------------- #
# Lectura del .docx
# --------------------------------------------------------------------------- #

W_P = re.compile(r"<w:p[^>]*/>|<w:p[ >].*?</w:p>", re.S)
W_TBL = re.compile(r"<w:tbl>.*?</w:tbl>", re.S)
# El orden de la alternancia importa: la forma autocerrada `<w:p .../>` va primero. Si no, el
# patrón con cierre la toma como apertura y busca el `</w:p>` siguiente, que está dentro de la
# tabla que viene después — y se traga la tabla entera sin dar ningún error.
W_BLOCK = re.compile(r"(<w:p[^>]*/>|<w:p[ >].*?</w:p>|<w:tbl>.*?</w:tbl>)", re.S)
W_TR = re.compile(r"<w:tr[ >].*?</w:tr>", re.S)
W_TC = re.compile(r"<w:tc[ >].*?</w:tc>", re.S)
W_T = re.compile(r"<w:t[^>]*>([^<]*)</w:t>")
W_OUTLINE = re.compile(r'<w:outlineLvl w:val="(\d+)"')
W_BR = re.compile(r"<w:(?:br|cr)/>")
W_PARA_IN_CELL = re.compile(r"<w:p[^>]*/>|<w:p[ >].*?</w:p>", re.S)


def texto(xml: str) -> str:
    """Texto plano de un fragmento, con los saltos de línea preservados."""
    xml = W_BR.sub("\n", xml)
    return "".join(W_T.findall(xml))


def texto_celda(xml: str) -> str:
    """Texto de una celda: cada párrafo interno es una línea."""
    partes = [texto(p).strip() for p in W_PARA_IN_CELL.findall(xml)]
    partes = [p for p in partes if p]
    return "\n".join(partes)


def filas(tabla: str) -> list[list[str]]:
    return [[texto_celda(c) for c in W_TC.findall(tr)] for tr in W_TR.findall(tabla)]


@dataclass
class Bloque:
    tipo: str  # "titulo" | "parrafo" | "tabla"
    nivel: int | None  # sólo en títulos
    texto: str
    tabla: list[list[str]] | None = None


def leer_documento(ruta: Path) -> list[Bloque]:
    with zipfile.ZipFile(ruta) as z:
        xml = z.read("word/document.xml").decode("utf-8")
    cuerpo = xml[xml.index("<w:body>") :]

    bloques: list[Bloque] = []
    for b in W_BLOCK.findall(cuerpo):
        if b.startswith("<w:tbl"):
            f = filas(b)
            if f:
                bloques.append(Bloque("tabla", None, "", f))
        else:
            t = texto(b).strip()
            m = W_OUTLINE.search(b)
            if m:
                bloques.append(Bloque("titulo", int(m.group(1)), t))
            elif t:
                bloques.append(Bloque("parrafo", None, t))
    return bloques


# --------------------------------------------------------------------------- #
# Reconocimiento de los artefactos
# --------------------------------------------------------------------------- #

RE_CU = re.compile(r"^CU-[A-Z]{3}-[A-Z]{3}$")
RE_CO = re.compile(r"^CO-\d{3}$")
RE_MODULO = re.compile(r"^\s*Módulos?\s+(\d+)(?:\s*a\s*\d+)?\s*[:\-–]\s*(.+)$")
RE_ID = re.compile(r"^(RF|RNF|OBJ|ACT|PA|DME)-\d+$")


@dataclass
class Modulo:
    numero: str
    nombre: str
    cus: list[str] = field(default_factory=list)
    contratos: list[str] = field(default_factory=list)


@dataclass
class CasoDeUso:
    codigo: str
    nombre: str
    modulo: str = ""
    resumen: list[list[str]] | None = None  # tarjeta de identificación
    ficha: list[list[str]] | None = None  # ficha extendida


@dataclass
class Contrato:
    codigo: str
    operacion: str
    modulo: str  # el módulo por posición en el documento
    tabla: list[list[str]]


def sin_tildes(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def slug(s: str) -> str:
    s = sin_tildes(s).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


def parsear(bloques: list[Bloque]):
    """Recorre el documento una vez y clasifica todo lo que reconoce."""
    cus: dict[str, CasoDeUso] = {}
    contratos: list[Contrato] = []
    modulos: dict[str, Modulo] = {}
    capitulos: dict[str, list[Bloque]] = {}

    capitulo_actual = ""
    modulo_actual = ""

    for b in bloques:
        if b.tipo == "titulo":
            if b.nivel == 0:
                capitulo_actual = b.texto
                capitulos.setdefault(capitulo_actual, [])
            m = RE_MODULO.match(b.texto)
            if m:
                num, nombre = m.group(1).zfill(2), m.group(2).strip()
                modulo_actual = num
                modulos.setdefault(num, Modulo(num, nombre))
            capitulos.setdefault(capitulo_actual, []).append(b)
            continue

        if b.tipo == "parrafo":
            capitulos.setdefault(capitulo_actual, []).append(b)
            continue

        # tabla
        primera = b.tabla[0] if b.tabla else []
        clave = primera[0].strip() if primera else ""

        if RE_CU.match(clave):
            nombre = primera[1].strip() if len(primera) > 1 else ""
            cu = cus.setdefault(clave, CasoDeUso(clave, nombre))
            if not cu.nombre:
                cu.nombre = nombre
            # la tarjeta de identificación es corta; la ficha extendida es larga
            if len(b.tabla) <= 5:
                cu.resumen = b.tabla
            else:
                cu.ficha = b.tabla
                cu.modulo = modulo_actual
                if clave not in modulos.get(modulo_actual, Modulo("", "")).cus:
                    if modulo_actual in modulos:
                        modulos[modulo_actual].cus.append(clave)
            continue

        if RE_CO.match(clave):
            operacion = primera[1].strip() if len(primera) > 1 else ""
            contratos.append(Contrato(clave, operacion, modulo_actual, b.tabla))
            if modulo_actual in modulos:
                modulos[modulo_actual].contratos.append(clave)
            continue

        capitulos.setdefault(capitulo_actual, []).append(b)

    return cus, contratos, modulos, capitulos


# --------------------------------------------------------------------------- #
# Lo que el script no toca
# --------------------------------------------------------------------------- #

# Archivos y carpetas bajo `.contexto-ia/` que mantiene el responsable a mano, o que genera otro
# script. Se comparan en minúsculas: el nombre en disco y el nombre con el que se los cita no
# siempre coinciden en las mayúsculas, y una comparación exacta dejaría de protegerlos sin avisar.
INTOCABLES = {
    "modelo_de_dominio.md",
    "tokens_visuales.md",
    "estructura.md",
    "identidad_visual.md",
    "detalles_funcionales_agregados.md",
    "openrouterapi.txt",
    "referencias-pantallas",
    "dss",
}


def es_intocable(rel: str) -> bool:
    """¿La ruta relativa cae dentro de algo que mantiene el responsable?"""
    return any(p.lower() in INTOCABLES for p in Path(rel).parts)


def huella_de(carpeta: Path) -> dict[str, str]:
    """Hash de cada archivo protegido, para comparar antes y después de la corrida."""
    huellas: dict[str, str] = {}
    if not carpeta.is_dir():
        return huellas
    for ruta in sorted(carpeta.rglob("*")):
        if ruta.is_file():
            rel = ruta.relative_to(carpeta).as_posix()
            if es_intocable(rel):
                huellas[rel] = hashlib.sha256(ruta.read_bytes()).hexdigest()
    return huellas


def comparar_huellas(antes: dict[str, str], despues: dict[str, str]) -> list[str]:
    """Qué les pasó a los archivos del responsable durante la corrida."""
    problemas = []
    for rel in sorted(antes):
        if rel not in despues:
            problemas.append(f"desapareció: {rel}")
        elif antes[rel] != despues[rel]:
            problemas.append(f"cambió: {rel}")
    return problemas


# --------------------------------------------------------------------------- #
# Las tres fuentes de operaciones
# --------------------------------------------------------------------------- #

RE_CU_EN_TEXTO = re.compile(r"CU-[A-Z]{3}-[A-Z]{3}")
RE_FILA_INVENTARIO = re.compile(r"^\|\s*(?:\*\*)?(OP-\d+)(?:\*\*)?\s*\|(.+?)\|", re.M)
RE_EVENTOS_DSS = re.compile(r"\*\*Eventos? del sistema:\*\*(.+)")
RE_NOMBRE_EN_BACKTICKS = re.compile(r"`([a-zA-Z][a-zA-Z0-9_]*)")

TOPE_DEL_INFORME = 12


RE_NOMBRE_AL_FRENTE = re.compile(r"^[`*\s]*([a-zA-Z][a-zA-Z0-9_]*)")


def nombre_de_operacion(texto_crudo: str) -> str:
    """El nombre pelado: sin backticks, sin argumentos, sin tipo de retorno, sin acotaciones.

    Se toma el identificador del frente y se descarta todo lo demás. Un contrato puede traer
    la operación anotada —«enviarPedidoConsolidado — *contrato de operación interna*»— y cortar
    sólo por el paréntesis dejaría la acotación pegada al nombre, inventando una diferencia
    entre fuentes que en realidad dicen lo mismo.
    """
    m = RE_NOMBRE_AL_FRENTE.match(texto_crudo.strip())
    return m.group(1) if m else ""


def _y_el_resto(nombres: list[str]) -> str:
    return " …" if len(nombres) > TOPE_DEL_INFORME else ""


def operaciones_del_inventario(ruta: Path) -> dict[str, str]:
    """`{nombre de operación: OP-nnn}` leído de `dss/inventario_operaciones.md`.

    Lo mantiene el responsable a mano. Si no está, el chequeo lo dice y sigue: que falte es una
    observación, no un motivo para no generar el contexto.
    """
    if not ruta.is_file():
        return {}
    operaciones: dict[str, str] = {}
    for op, celda in RE_FILA_INVENTARIO.findall(ruta.read_text(encoding="utf-8")):
        nombre = nombre_de_operacion(celda)
        if nombre:
            operaciones[nombre] = op
    return operaciones


def operaciones_de_los_dss(carpeta: Path) -> dict[str, str]:
    """`{nombre de operación: archivo del DSS donde aparece}`.

    Sale de las líneas «**Eventos del sistema:** `x`, `y`» que cierran cada diagrama, y no de
    leer el PlantUML: el diagrama muestra también los mensajes de vuelta y las notas, que no son
    operaciones. La línea de eventos es la declaración explícita de quien lo dibujó.
    """
    if not carpeta.is_dir():
        return {}
    operaciones: dict[str, str] = {}
    for ruta in sorted(carpeta.glob("[0-9]*.md")):
        for linea in RE_EVENTOS_DSS.findall(ruta.read_text(encoding="utf-8")):
            for nombre in RE_NOMBRE_EN_BACKTICKS.findall(linea):
                operaciones.setdefault(nombre, ruta.name)
    return operaciones


def revisar_operaciones(contratos, inventario, dss) -> list[str]:
    """Compara las tres fuentes **por nombre de operación**.

    Una operación se vincula con su contrato por el nombre y nunca por un número de operación.
    El inventario numera `OP-nnn` y declara que a cada uno le corresponde un `C-nnn` con el
    mismo número: eso es una afirmación del documento, y es exactamente lo que hay que
    comprobar en lugar de suponerlo.

    Informa y no corrige. Las diferencias van a `docs/DEUDA.md`.
    """
    por_nombre: dict[str, list[str]] = {}
    for co in contratos:
        nombre = nombre_de_operacion(co.operacion)
        if nombre:
            por_nombre.setdefault(nombre, []).append(co.codigo)

    observaciones: list[str] = []

    sin_contrato = sorted(set(inventario) - set(por_nombre))
    if sin_contrato:
        observaciones.append(
            f"{len(sin_contrato)} operación(es) del inventario sin contrato volcado: "
            + ", ".join(f"{n} ({inventario[n]})" for n in sin_contrato[:TOPE_DEL_INFORME])
            + _y_el_resto(sin_contrato)
        )

    sin_inventario = sorted(set(por_nombre) - set(inventario))
    if sin_inventario:
        observaciones.append(
            f"{len(sin_inventario)} contrato(s) cuya operación no figura en el inventario: "
            + ", ".join(f"{n} ({por_nombre[n][0]})" for n in sin_inventario[:TOPE_DEL_INFORME])
            + _y_el_resto(sin_inventario)
        )

    sin_dss = sorted(set(inventario) - set(dss))
    if sin_dss:
        observaciones.append(
            f"{len(sin_dss)} operación(es) del inventario que ningún DSS declara: "
            + ", ".join(sin_dss[:TOPE_DEL_INFORME])
            + _y_el_resto(sin_dss)
        )

    solo_dss = sorted(set(dss) - set(inventario))
    if solo_dss:
        observaciones.append(
            f"{len(solo_dss)} operación(es) de un DSS ausente(s) del inventario: "
            + ", ".join(f"{n} ({dss[n]})" for n in solo_dss[:TOPE_DEL_INFORME])
            + _y_el_resto(solo_dss)
        )

    # El inventario declara en su cabecera que «cada operación tiene exactamente un contrato
    # C-nnn con el mismo número». Eso es una afirmación del documento, y se comprueba buscando
    # el contrato por el **nombre** de la operación y mirando qué número resultó tener.
    #
    # Va como una sola observación y no como una lista: si la convención no se cumple, lo que
    # hay que registrar en DEUDA es que la numeración no sirve para vincular, no doscientas
    # líneas diciendo lo mismo. El vínculo que sí sirve es el nombre, y por eso es el que este
    # chequeo usa.
    emparejados = {n: op for n, op in inventario.items() if n in por_nombre}
    desajustes = [
        f"{n} ({op} ↔ {', '.join(por_nombre[n])})"
        for n, op in sorted(emparejados.items())
        if f"CO-{op.split('-')[1]}" not in por_nombre[n]
    ]
    if desajustes:
        observaciones.append(
            f"la numeración OP-nnn ↔ C-nnn que el inventario declara no se cumple en "
            f"{len(desajustes)} de {len(emparejados)} operaciones. Es la afirmación del "
            f"inventario la que no se sostiene, no las operaciones: el vínculo que sí funciona "
            f"es el nombre, y por él las tres fuentes se corresponden. Ejemplos: "
            + "; ".join(desajustes[:5])
        )

    repetidos = sorted(n for n, codigos in por_nombre.items() if len(codigos) > 1)
    if repetidos:
        observaciones.append(
            f"{len(repetidos)} nombre(s) de operación con más de un contrato: "
            + "; ".join(f"{n} → {', '.join(por_nombre[n])}" for n in repetidos[:TOPE_DEL_INFORME])
            + _y_el_resto(repetidos)
        )

    return observaciones


# --------------------------------------------------------------------------- #
# Dónde va cada contrato
# --------------------------------------------------------------------------- #

ARCHIVO_TRANSVERSAL = "00-transversales.md"


def modulos_referenciados(co: Contrato, cus: dict[str, CasoDeUso]) -> set[str]:
    """Los módulos donde viven los casos de uso que el contrato declara referenciar."""
    fila = next((f for f in co.tabla if f and "referencias" in f[0].strip().lower()), None)
    if not fila or len(fila) < 2:
        return set()
    codigos = set(RE_CU_EN_TEXTO.findall(fila[1]))
    return {cus[c].modulo for c in codigos if c in cus and cus[c].modulo}


def archivo_de_contrato(co, cus, archivos_por_modulo) -> tuple[str, set[str]]:
    """El archivo donde se archiva el contrato, y los módulos que lo reclaman.

    Tres casos, en orden:

    - **Un solo módulo** entre sus referencias: el archivo de ese módulo.
    - **Más de uno**: `00-transversales.md`. No pertenece a ninguno, y elegir el primero
      escondería justamente el hecho de que es transversal.
    - **Ninguno** —el contrato no referencia ningún caso de uso, o los que referencia no tienen
      ficha—: se cae a la posición que ocupa en el documento, que es lo único que queda, y la
      verificación lo reporta.
    """
    modulos = modulos_referenciados(co, cus)
    if len(modulos) == 1:
        return archivos_por_modulo.get(next(iter(modulos)), ARCHIVO_TRANSVERSAL), modulos
    if len(modulos) > 1:
        return ARCHIVO_TRANSVERSAL, modulos
    return archivos_por_modulo.get(co.modulo, ARCHIVO_TRANSVERSAL), modulos


# --------------------------------------------------------------------------- #
# Escritura
# --------------------------------------------------------------------------- #

CABECERA = (
    "> **Generado por `scripts/generar_contexto.py` desde el documento de análisis.**\n"
    "> No lo edites: la próxima corrida lo pisa. Si algo está mal, anotalo en la bitácora "
    "del módulo.\n\n"
)


def tabla_md(t: list[list[str]], omitir_primera: bool = False) -> str:
    """Una tabla del documento como tabla Markdown, o como lista de campos si es de dos columnas."""
    if not t:
        return ""
    if omitir_primera:
        t = t[1:]
        if not t:
            return ""
    ancho = max(len(f) for f in t)

    # Tabla de dos columnas: es una ficha (campo | valor). Las filas de una sola celda son
    # títulos de sección dentro de la ficha; cortan la tabla y abren una nueva, porque si no las
    # filas que siguen quedan sin encabezado y Markdown no las rinde como tabla.
    if ancho <= 2:
        salida: list[str] = []
        abierta = False

        def abrir() -> None:
            nonlocal abierta
            salida.append("| Campo | Valor |")
            salida.append("| --- | --- |")
            abierta = True

        for fila in t:
            if len(fila) == 1 or (len(fila) == 2 and not fila[1].strip()):
                salida.append("")
                salida.append(f"**{fila[0]}**")
                salida.append("")
                abierta = False
            elif len(fila) >= 2:
                if not abierta:
                    abrir()
                valor = fila[1].replace("\n", "<br>")
                salida.append(f"| {fila[0]} | {valor} |")
        return "\n".join(salida).strip()

    encabezado = t[0] + [""] * (ancho - len(t[0]))
    sep = ["---"] * ancho
    lineas = [
        "| " + " | ".join(c.replace("\n", "<br>") for c in encabezado) + " |",
        "| " + " | ".join(sep) + " |",
    ]
    for fila in t[1:]:
        fila = fila + [""] * (ancho - len(fila))
        lineas.append("| " + " | ".join(c.replace("\n", "<br>") for c in fila) + " |")
    return "\n".join(lineas)


def escribir(ruta: Path, contenido: str) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(CABECERA + contenido.rstrip() + "\n", encoding="utf-8")


def volcar_capitulo(bloques: list[Bloque], titulo: str) -> str:
    partes = [f"# {titulo}\n"]
    for b in bloques:
        if b.tipo == "titulo":
            if not b.texto:
                continue
            partes.append("\n" + "#" * min(b.nivel + 2, 6) + f" {b.texto}\n")
        elif b.tipo == "parrafo":
            partes.append(b.texto + "\n")
        elif b.tipo == "tabla":
            partes.append("\n" + tabla_md(b.tabla) + "\n")
    return "\n".join(partes)


# --------------------------------------------------------------------------- #
# Principal
# --------------------------------------------------------------------------- #

# Capítulos del documento que se vuelcan tal cual, y a qué archivo van.
CAPITULOS = {
    "CONTEXTO.md": ["Contexto y Escenario", "Introducción y Planificación del Proyecto"],
    "ALCANCE.md": [
        "Alcance y Limitaciones",
        "Artefactos Complementarios de la Visión y el Modelo de Casos de Uso",
    ],
    "REQUISITOS.md": ["Requisitos"],
}


def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--docx", type=Path, default=Path("docs/Longbox - Comic Store Manager.docx"))
    p.add_argument("--salida", type=Path, default=Path(".contexto-ia"))
    p.add_argument("--dry-run", action="store_true", help="informa sin escribir nada")
    args = p.parse_args()

    if not args.docx.is_file():
        print(f"error: no existe {args.docx}", file=sys.stderr)
        return 1

    # La huella se toma *antes* de escribir nada: es contra esto que se compara al final.
    huella_inicial = huella_de(args.salida)

    bloques = leer_documento(args.docx)
    cus, contratos, modulos, capitulos = parsear(bloques)

    print(f"Documento  : {args.docx}")
    print(f"Salida     : {args.salida}/")
    print(f"Módulos    : {len(modulos)}")
    print(f"Casos de uso: {len(cus)}  ·  Contratos: {len(contratos)}")
    if args.dry_run:
        print("Modo       : dry-run, no se escribe nada\n")

    def emitir(rel: str, contenido: str) -> None:
        if es_intocable(rel):
            return
        if not args.dry_run:
            escribir(args.salida / rel, contenido)

    # --- capítulos volcados tal cual ---
    for archivo, nombres in CAPITULOS.items():
        partes = []
        for n in nombres:
            if n in capitulos:
                partes.append(volcar_capitulo(capitulos[n], n))
        if partes:
            emitir(archivo, "\n\n---\n\n".join(partes))

    # --- actores y procesos automatizados ---
    modelado = capitulos.get("Modelado", [])
    if modelado:
        emitir(
            "ACTORES.md",
            volcar_capitulo(
                [
                    b
                    for b in modelado
                    if b.tipo != "tabla"
                    or (b.tabla and b.tabla[0] and RE_ID.match(b.tabla[0][0].strip()))
                ],
                "Actores y procesos automatizados",
            ),
        )

    archivos_por_modulo = {num: f"{num}-{slug(mod.nombre)}.md" for num, mod in modulos.items()}

    # --- fichas, por módulo ---
    for num, mod in sorted(modulos.items()):
        propios = [c for c in cus.values() if c.modulo == num and c.ficha]
        if not propios:
            continue
        partes = [
            f"# Módulo {num} · {mod.nombre}\n",
            "Fichas extendidas de los casos de uso del módulo.\n",
        ]
        for cu in sorted(propios, key=lambda c: c.codigo):
            partes.append(f"\n---\n\n## {cu.codigo} · {cu.nombre}\n")
            if cu.resumen:
                partes.append(tabla_md(cu.resumen, omitir_primera=True) + "\n")
            partes.append(tabla_md(cu.ficha, omitir_primera=True) + "\n")
        emitir(f"cu/{archivos_por_modulo[num]}", "\n".join(partes))

    # --- contratos, por sus Referencias Cruzadas ---
    por_archivo: dict[str, list[Contrato]] = {}
    mal_archivados: list[str] = []
    for co in contratos:
        archivo, reclamantes = archivo_de_contrato(co, cus, archivos_por_modulo)
        por_archivo.setdefault(archivo, []).append(co)
        if archivo != ARCHIVO_TRANSVERSAL:
            modulo_del_archivo = archivo.split("-")[0]
            if modulo_del_archivo not in reclamantes:
                mal_archivados.append(
                    f"{co.codigo} → {archivo} "
                    + (
                        f"(sus CU viven en {', '.join(sorted(reclamantes))})"
                        if reclamantes
                        else "(no referencia ningún caso de uso con ficha; archivado por posición)"
                    )
                )

    for archivo, propios_co in sorted(por_archivo.items()):
        if archivo == ARCHIVO_TRANSVERSAL:
            titulo = "# Contratos transversales\n"
            intro = (
                "Contratos cuyas Referencias Cruzadas nombran casos de uso de **más de un "
                "módulo**. No pertenecen a ninguno.\n"
            )
        else:
            num = archivo.split("-")[0]
            mod = modulos.get(num)
            titulo = f"# Módulo {num} · {mod.nombre if mod else ''}\n"
            intro = "Contratos de operación del módulo.\n"
        partes = [titulo, intro]
        for co in sorted(propios_co, key=lambda c: c.codigo):
            partes.append(f"\n---\n\n## {co.codigo} · {co.operacion}\n")
            partes.append(tabla_md(co.tabla, omitir_primera=True) + "\n")
        emitir(f"contratos/{archivo}", "\n".join(partes))

    # --- índice ---
    lineas = [
        "# Índice de casos de uso\n",
        "Punto de entrada. Ubicá el caso de uso y abrí los cuatro archivos de su módulo: "
        "ficha, DSS, contratos y el modelo de dominio en las entidades que toca.\n",
        "Los contratos se archivan por sus Referencias Cruzadas. Los que nombran casos de "
        "uso de más de un módulo viven en `contratos/00-transversales.md`.\n",
        "El estado de construcción **no está acá**: vive en `docs/ESTADO.md`.\n",
        "\n| Caso de uso | Nombre | Módulo | Ficha | DSS | Contratos |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for cod, cu in sorted(cus.items()):
        mod = modulos.get(cu.modulo)
        if not mod:
            lineas.append(f"| `{cod}` | {cu.nombre} | — | — | — | — |")
            continue
        arch = archivos_por_modulo[mod.numero]
        lineas.append(
            f"| `{cod}` | {cu.nombre} | {mod.numero} {mod.nombre} "
            f"| `cu/{arch}` | `dss/{arch}` | `contratos/{arch}` |"
        )
    emitir("INDICE.md", "\n".join(lineas))

    # --- verificación --------------------------------------------------- #
    print("\nVerificación")
    problemas = 0

    sin_ficha = [c for c, cu in sorted(cus.items()) if not cu.ficha]
    if sin_ficha:
        problemas += len(sin_ficha)
        print(
            f"  · {len(sin_ficha)} caso(s) de uso con tarjeta pero sin ficha extendida: "
            f"{', '.join(sin_ficha)}"
        )

    sin_modulo = [c for c, cu in sorted(cus.items()) if cu.ficha and not cu.modulo]
    if sin_modulo:
        problemas += len(sin_modulo)
        print(f"  · {len(sin_modulo)} ficha(s) fuera de todo módulo: {', '.join(sin_modulo)}")

    vacios = [f"{m.numero} {m.nombre}" for m in modulos.values() if not m.cus]
    if vacios:
        print(f"  · {len(vacios)} módulo(s) sin fichas: {', '.join(vacios)}")

    # numeración de contratos sin huecos
    nums = sorted(int(c.codigo.split("-")[1]) for c in contratos)
    huecos = [n for n in range(1, (nums[-1] if nums else 0) + 1) if n not in nums]
    if huecos:
        problemas += len(huecos)
        print(
            f"  · {len(huecos)} hueco(s) en la numeración de contratos: "
            f"{', '.join(f'CO-{n:03d}' for n in huecos)}"
        )

    faltantes = [n for grupo in CAPITULOS.values() for n in grupo if n not in capitulos]
    if faltantes:
        problemas += len(faltantes)
        print(f"  · capítulo(s) esperados y no encontrados: {', '.join(faltantes)}")

    # el chequeo que faltaba el 2026-09-14
    if mal_archivados:
        problemas += len(mal_archivados)
        print(
            f"  · {len(mal_archivados)} contrato(s) archivado(s) donde ninguno de sus casos de "
            f"uso vive:"
        )
        for aviso in mal_archivados[:TOPE_DEL_INFORME]:
            print(f"      {aviso}")
        if len(mal_archivados) > TOPE_DEL_INFORME:
            print(f"      … y {len(mal_archivados) - TOPE_DEL_INFORME} más")

    transversales = por_archivo.get(ARCHIVO_TRANSVERSAL, [])
    print(f"  · {len(transversales)} contrato(s) transversal(es) en {ARCHIVO_TRANSVERSAL}")

    # --- consistencia por nombre de operación --------------------------- #
    inventario = operaciones_del_inventario(args.salida / "dss" / "inventario_operaciones.md")
    dss = operaciones_de_los_dss(args.salida / "dss")

    print("\nConsistencia de operaciones (por nombre, no por número)")
    print(f"  Contratos: {len(contratos)}  ·  Inventario: {len(inventario)}  ·  DSS: {len(dss)}")
    if not inventario:
        print("  · no se encontró dss/inventario_operaciones.md")
    if not dss:
        print("  · no se encontró ningún DSS en dss/")
    avisos = revisar_operaciones(contratos, inventario, dss)
    for aviso in avisos:
        print(f"  · {aviso}")
    if not avisos and inventario and dss:
        print("  Las tres fuentes coinciden.")
    print("  El chequeo informa y no corrige: las diferencias van a docs/DEUDA.md.")

    if not problemas:
        print("\nSin observaciones sobre la estructura del documento.")

    # --- lo que el responsable mantiene --------------------------------- #
    tocados = comparar_huellas(huella_inicial, huella_de(args.salida))
    print(f"\nArchivos del responsable: {len(huella_inicial)} protegido(s)")
    if tocados:
        print("  ERROR: la corrida tocó archivos que no le pertenecen:", file=sys.stderr)
        for aviso in tocados:
            print(f"    · {aviso}", file=sys.stderr)
        return 2
    print("  Ninguno desapareció ni cambió.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
