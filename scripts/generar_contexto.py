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
    .contexto-ia/dss/DSS.md                   los diagramas de secuencia del sistema
    .contexto-ia/TOKENS_VISUALES.md
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

Los DSS tampoco se generan: en el documento son figuras, y su fuente es `dss/DSS.md`, un apartado
`### CU-MOD-AAA · Nombre` por caso de uso con sus diagramas y la línea «**Eventos del sistema:**»
de cada uno. El script lo lee para verificar, nunca lo escribe.

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
`contratos/00-transversales.md`. Es el caso de `CO-156 cancelarOperacion`, referenciado por
casos de uso de varios módulos.

Verificación
------------
El script no falla en silencio. Al terminar informa qué esperaba encontrar y no encontró.

Estructura del documento:

1. Fichas sin tarjeta, tarjetas sin ficha, fichas fuera de módulo, módulos vacíos.
2. Códigos repetidos: dos fichas o dos tarjetas de identificación con el mismo código. Una ficha
   rotulada con el código de otra deja a la segunda sin ficha y la pisa en silencio.
3. Nombre distinto entre la tarjeta de identificación y la ficha de un mismo caso de uso.
4. Huecos en la numeración de contratos (los retirados no cuentan como hueco) y contratos
   retirados que siguen definidos.
5. Estructura de cada contrato: los ocho campos en su orden, la firma en «Nombre y Tipo» con el
   nombre de la operación del encabezado, y al menos un caso de uso en «Referencias Cruzadas».
   Un contrato con los valores corridos un campo pasa todos los chequeos por nombre de campo y
   sólo lo delata el contenido.
6. **Contratos archivados donde ninguno de sus casos de uso vive.** Es el chequeo que faltaba el
   2026-09-14.

Referencias en el texto:

7. Menciones a casos de uso que no tienen ficha, en cualquier parte del documento. Si el código
   es de un caso de uso retirado, se lo marca como tal.
8. Menciones a pasos, alternativas o excepciones que la ficha citada no tiene («paso 6 de
   CU-TDA-CMP», «CU-TDA-CRC (A2, A3)»).
9. Asimetría de trazabilidad: el caso de uso cita un requisito que no lo lista en «CU
   Asociados», o al revés. Un requisito cuya fila «CU Asociados» dice «Transversal» no pide
   que se enumeren los casos de uso que lo citan.

Operaciones, **por nombre** y nunca por número:

10. Casos de uso sin apartado en `dss/DSS.md`, y apartados de casos de uso sin ficha.
11. Por caso de uso: operaciones de su DSS que ningún contrato con ese caso de uso en sus
    Referencias Cruzadas declara, y operaciones de esos contratos que su DSS no muestra.
12. Operaciones de un DSS sin ningún contrato, y contratos cuya operación no aparece en ningún DSS.
13. Nombres de operación con más de un contrato.

Y al final, que los archivos del responsable sigan como estaban.

**El chequeo informa y no corrige.** Las diferencias van a `docs/DEUDA.md`, que es donde vive la
distancia entre lo especificado y lo construido. Un generador que ajusta lo que encuentra deja de
ser un volcado y pasa a ser una interpretación.

Con `--estricto`, sale con código 1 si hubo observaciones de estructura o de referencias. Sin él,
informa y sale con 0, salvo que se hayan tocado archivos del responsable (código 2).
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
    nombre_tarjeta: str = ""
    nombre_ficha: str = ""
    # cuántas veces aparece cada tabla con este código: más de una es un código mal puesto
    tarjetas: int = 0
    fichas: int = 0

    def identificadores(self) -> set[str]:
        """Pasos, alternativas y excepciones que la ficha declara: «3», «A1», «E2».

        Una fila puede agrupar varios pasos («7 a 9»): cuenta como cada uno de ellos.
        """
        ids: set[str] = set()
        for f in self.ficha or []:
            clave = f[0].strip() if f else ""
            rango = re.fullmatch(r"(\d+)\s*(?:a|-|–)\s*(\d+)", clave)
            if rango:
                ids |= {str(n) for n in range(int(rango[1]), int(rango[2]) + 1)}
            elif re.fullmatch(r"\d+|[AE]\d+", clave):
                ids.add(clave)
        return ids


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
            # la tarjeta de identificación es corta; la ficha extendida es larga
            if len(b.tabla) <= 5:
                cu.tarjetas += 1
                if cu.resumen is None:
                    cu.resumen = b.tabla
                    cu.nombre_tarjeta = nombre
            else:
                cu.fichas += 1
                # Si el código se repite, se conserva la primera ficha y la verificación lo
                # informa. Pisarla con la segunda escondería el error bajo otro error.
                if cu.ficha is None:
                    cu.ficha = b.tabla
                    cu.nombre_ficha = nombre
                    cu.nombre = nombre  # el nombre canónico es el de la ficha
                    cu.modulo = modulo_actual
                    if modulo_actual in modulos and clave not in modulos[modulo_actual].cus:
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
# Bajas registradas en el documento
# --------------------------------------------------------------------------- #

# Códigos dados de baja. No se reutilizan: un contrato retirado deja su número vacante, y ese
# hueco no es un error de numeración. Un código de esta lista que siga definido o mencionado en
# el documento sí lo es, y la verificación lo informa como tal.
CU_RETIRADOS = {
    "CU-CFG-EDT",
    "CU-CFG-TIP",
    "CU-CAT-ETQ",
    "CU-PVP-TAB",
    "CU-CFG-BAN",
    "CU-TDA-CAR",
    "CU-STK-ADM",
}
CO_RETIRADOS = {"CO-046", "CO-143"}

# Códigos que el documento usa como ejemplo de formato y no como referencia.
CODIGOS_DE_EJEMPLO = {"CU-MOD-AAA"}

# Los ocho campos de un contrato, en su orden.
CAMPOS_DE_CONTRATO = [
    "Nombre y Tipo",
    "Responsabilidades",
    "Referencias Cruzadas",
    "Notas",
    "Excepciones",
    "Salida",
    "Precondiciones",
    "Postcondiciones",
]


# --------------------------------------------------------------------------- #
# Operaciones: contratos y DSS
# --------------------------------------------------------------------------- #

RE_CU_EN_TEXTO = re.compile(r"CU-[A-Z]{3}-[A-Z]{3}")
RE_REQ_EN_TEXTO = re.compile(r"\bR(?:N)?F-\d+\b")
RE_EVENTOS_DSS = re.compile(r"\*\*Eventos? del sistema:?\*\*:?(.+)")
RE_NOMBRE_EN_BACKTICKS = re.compile(r"`([a-zA-Z][a-zA-Z0-9_]*)")
RE_NOMBRE_CAMEL = re.compile(r"\b[a-z]+[A-Z][a-zA-Z0-9]*\b")
RE_APARTADO_DSS = re.compile(r"^###\s+(CU-[A-Z]{3}-[A-Z]{3})\b", re.M)

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


def _lista(nombres, tope: int = TOPE_DEL_INFORME) -> str:
    nombres = list(nombres)
    return ", ".join(nombres[:tope]) + (
        f" … y {len(nombres) - tope} más" if len(nombres) > tope else ""
    )


def campo(co: Contrato, nombre: str) -> str:
    fila = next((f for f in co.tabla[1:] if f and f[0].strip() == nombre), None)
    return fila[1].strip() if fila and len(fila) > 1 else ""


def cus_del_contrato(co: Contrato) -> set[str]:
    return set(RE_CU_EN_TEXTO.findall(campo(co, "Referencias Cruzadas")))


def leer_dss(ruta: Path) -> tuple[dict[str, list[str]], list[str]]:
    """`({CU: [operaciones]}, [operaciones sin caso de uso])` leído de `dss/DSS.md`.

    Cada apartado `### CU-MOD-AAA · Nombre` reúne las líneas «**Eventos del sistema:**» de sus
    diagramas. Se lee esa línea y no el PlantUML: el diagrama muestra también los mensajes de
    vuelta y las notas, que no son operaciones. La línea de eventos es la declaración explícita
    de quien lo dibujó. Los nombres se aceptan con o sin backticks.

    Lo que viene después de un encabezado `##` sin caso de uso (un anexo) se reúne aparte.
    """
    if not ruta.is_file():
        return {}, []
    por_cu: dict[str, list[str]] = {}
    sin_cu: list[str] = []
    actual: str | None = None
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        m = RE_APARTADO_DSS.match(linea)
        if m:
            actual = m.group(1)
            por_cu.setdefault(actual, [])
            continue
        if re.match(r"^##\s", linea):
            actual = None
            continue
        e = RE_EVENTOS_DSS.search(linea)
        if not e:
            continue
        nombres = RE_NOMBRE_EN_BACKTICKS.findall(e.group(1)) or RE_NOMBRE_CAMEL.findall(e.group(1))
        destino = por_cu[actual] if actual else sin_cu
        for n in nombres:
            if n not in destino:
                destino.append(n)
    return por_cu, sin_cu


# --------------------------------------------------------------------------- #
# Verificaciones
# --------------------------------------------------------------------------- #


def revisar_casos_de_uso(cus: dict[str, CasoDeUso]) -> list[str]:
    obs: list[str] = []
    rep_f = [f"{c} ({cu.fichas})" for c, cu in sorted(cus.items()) if cu.fichas > 1]
    if rep_f:
        obs.append(f"{len(rep_f)} código(s) con más de una ficha extendida: {_lista(rep_f)}")
    rep_t = [f"{c} ({cu.tarjetas})" for c, cu in sorted(cus.items()) if cu.tarjetas > 1]
    if rep_t:
        obs.append(
            f"{len(rep_t)} código(s) con más de una tarjeta de identificación: {_lista(rep_t)}"
        )
    sin_ficha = [c for c, cu in sorted(cus.items()) if not cu.ficha]
    if sin_ficha:
        obs.append(
            f"{len(sin_ficha)} caso(s) de uso con tarjeta pero sin ficha extendida: "
            f"{_lista(sin_ficha)}"
        )
    sin_tarjeta = [c for c, cu in sorted(cus.items()) if cu.ficha and not cu.resumen]
    if sin_tarjeta:
        obs.append(
            f"{len(sin_tarjeta)} ficha(s) sin tarjeta de identificación: {_lista(sin_tarjeta)}"
        )
    sin_modulo = [c for c, cu in sorted(cus.items()) if cu.ficha and not cu.modulo]
    if sin_modulo:
        obs.append(f"{len(sin_modulo)} ficha(s) fuera de todo módulo: {_lista(sin_modulo)}")
    nombres = [
        f"{c}: tarjeta «{cu.nombre_tarjeta}» / ficha «{cu.nombre_ficha}»"
        for c, cu in sorted(cus.items())
        if cu.resumen
        and cu.ficha
        and " ".join(cu.nombre_tarjeta.split()) != " ".join(cu.nombre_ficha.split())
    ]
    if nombres:
        obs.append(f"{len(nombres)} caso(s) de uso con nombre distinto en tarjeta y ficha:")
        obs += [f"    {n}" for n in nombres]
    retirados = sorted(c for c in cus if c in CU_RETIRADOS)
    if retirados:
        obs.append(
            f"{len(retirados)} caso(s) de uso retirado(s) que siguen definidos: {_lista(retirados)}"
        )
    return obs


def revisar_contratos(contratos: list[Contrato]) -> list[str]:
    obs: list[str] = []
    nums = sorted(int(c.codigo.split("-")[1]) for c in contratos)
    retirados = {int(c.split("-")[1]) for c in CO_RETIRADOS}
    huecos = [
        n for n in range(1, (nums[-1] if nums else 0) + 1) if n not in nums and n not in retirados
    ]
    if huecos:
        obs.append(
            f"{len(huecos)} hueco(s) en la numeración de contratos: "
            f"{_lista(f'CO-{n:03d}' for n in huecos)}"
        )
    vigentes = sorted({c.codigo for c in contratos} & CO_RETIRADOS)
    if vigentes:
        obs.append(
            f"{len(vigentes)} contrato(s) retirado(s) que siguen definidos: {_lista(vigentes)}"
        )
    repetidos = sorted(
        {c.codigo for c in contratos if [x.codigo for x in contratos].count(c.codigo) > 1}
    )
    if repetidos:
        obs.append(f"{len(repetidos)} código(s) de contrato repetido(s): {_lista(repetidos)}")

    mal: list[str] = []
    for co in contratos:
        etiquetas = [f[0].strip() for f in co.tabla[1:] if f]
        nombre = nombre_de_operacion(co.operacion)
        firma = campo(co, "Nombre y Tipo")
        faltas = []
        if etiquetas != CAMPOS_DE_CONTRATO:
            faltas.append("campos distintos de los ocho esperados o en otro orden")
        if nombre_de_operacion(firma) != nombre:
            faltas.append(f"«Nombre y Tipo» no empieza por {nombre}")
        elif "(" not in firma:
            faltas.append("«Nombre y Tipo» sin firma (faltan los parámetros)")
        if not re.search(r"CU-[A-Z]{3}-[A-Z]{3}|PA-\d+", campo(co, "Referencias Cruzadas")):
            faltas.append("«Referencias Cruzadas» sin caso de uso")
        for c in ("Precondiciones", "Postcondiciones"):
            if not campo(co, c):
                faltas.append(f"«{c}» vacío")
        if faltas:
            mal.append(f"{co.codigo} {nombre}: {'; '.join(faltas)}")
    if mal:
        obs.append(f"{len(mal)} contrato(s) con la estructura alterada:")
        obs += [f"    {m}" for m in mal]
    return obs


RE_REF_TRAS_CODIGO = re.compile(
    r"(CU-[A-Z]{3}-[A-Z]{3})"
    r"(\s*\((?:pasos?|flujo principal|[AE]\d)[^)]*\)|(?:\s+[AE]\d+(?:\s*(?:,|/|y)\s*[AE]?\d+)*))"
)
RE_REF_ANTES_DE_CODIGO = re.compile(
    r"\b(pasos?\s+\d+(?:\s*(?:,|y|a|-)\s*\d+)*|[AE]\d+)\s+de\s+(CU-[A-Z]{3}-[A-Z]{3})"
)


def _identificadores_citados(cola: str) -> list[str]:
    """«(pasos 4-5)» → 4, 5 · «(paso 3)» → 3 · «A2, A3 y A4» → A2, A3, A4."""
    ids: list[str] = []
    for a, b in re.findall(r"(\d+)\s*(?:-|a)\s*(\d+)", cola):
        if "paso" in cola:
            ids += [str(x) for x in range(int(a), int(b) + 1)]
    if "paso" in cola and not ids:
        ids = re.findall(r"(?<![AE\d])\d+", cola)
    ids += re.findall(r"[AE]\d+", cola)
    return ids


def textos_del_documento(bloques: list[Bloque]):
    """(dónde, texto) de cada párrafo y de cada tabla, para buscar menciones."""
    capitulo = ""
    for b in bloques:
        if b.tipo == "titulo":
            if b.nivel == 0:
                capitulo = b.texto
            continue
        if b.tipo == "parrafo":
            yield f"§ {capitulo[:40]}", b.texto
        else:
            clave = b.tabla[0][0].strip() if b.tabla and b.tabla[0] else ""
            donde = (
                clave
                if re.match(r"^(CU|CO|RF|RNF|PA|BR|I|PD|DME)-", clave)
                else f"tabla en § {capitulo[:40]}"
            )
            yield donde, "\n".join(" | ".join(f) for f in b.tabla)


def revisar_referencias(bloques: list[Bloque], cus: dict[str, CasoDeUso]) -> list[str]:
    obs: list[str] = []
    con_ficha = {c: cu for c, cu in cus.items() if cu.ficha}

    # menciones a casos de uso sin ficha
    menciones: dict[str, list[str]] = {}
    pasos_mal: list[str] = []
    for donde, t in textos_del_documento(bloques):
        for c in set(RE_CU_EN_TEXTO.findall(t)):
            if c not in con_ficha and c not in CODIGOS_DE_EJEMPLO:
                menciones.setdefault(c, []).append(donde)
        citas = [(m.group(1), m.group(2)) for m in RE_REF_TRAS_CODIGO.finditer(t)]
        citas += [(m.group(2), m.group(1)) for m in RE_REF_ANTES_DE_CODIGO.finditer(t)]
        for c, cola in citas:
            if c not in con_ficha:
                continue
            faltan = [
                i for i in _identificadores_citados(cola) if i not in con_ficha[c].identificadores()
            ]
            if faltan:
                pasos_mal.append(
                    f"{donde}: «{c} {cola.strip()}» cita {', '.join(faltan)}, que la ficha no tiene"
                )
    if menciones:
        obs.append(f"{len(menciones)} código(s) de caso de uso mencionado(s) sin ficha extendida:")
        for c in sorted(menciones):
            marca = " (retirado)" if c in CU_RETIRADOS else ""
            lugares = sorted(set(menciones[c]))
            obs.append(f"    {c}{marca}: {len(menciones[c])} mención(es) en {_lista(lugares, 8)}")
    if pasos_mal:
        obs.append(
            f"{len(pasos_mal)} mención(es) a pasos, alternativas o excepciones inexistentes:"
        )
        obs += [f"    {p}" for p in pasos_mal]
    return obs


def revisar_trazabilidad(bloques: list[Bloque], cus: dict[str, CasoDeUso]) -> list[str]:
    """Requisitos Asociados de cada ficha contra CU Asociados de cada requisito."""
    cu_req: dict[str, set[str]] = {}
    for c, cu in cus.items():
        fila = next(
            (f for f in (cu.ficha or []) if f and f[0].strip() == "Requisitos Asociados"), None
        )
        if fila and len(fila) > 1:
            cu_req[c] = set(RE_REQ_EN_TEXTO.findall(fila[1]))
    req_cu: dict[str, set[str]] = {}
    # Un requisito es transversal cuando su fila «CU Asociados» lo declara así: rige para
    # todos los casos de uso y no los enumera. Las fichas lo siguen citando, y esa cita no pide
    # reciprocidad. Los casos de uso que sí enumera se siguen verificando.
    transversales: set[str] = set()
    for b in bloques:
        if b.tipo != "tabla" or not b.tabla or not b.tabla[0]:
            continue
        clave = b.tabla[0][0].strip()
        if re.fullmatch(r"R(?:N)?F-\d+", clave):
            fila = next((f for f in b.tabla if f and f[0].strip() == "CU Asociados"), None)
            if fila and len(fila) > 1:
                req_cu[clave] = set(RE_CU_EN_TEXTO.findall(fila[1]))
                if "transversal" in fila[1].lower():
                    transversales.add(clave)
    a = sorted(
        f"{c} cita {r}"
        for c, rs in cu_req.items()
        for r in rs
        if r in req_cu and r not in transversales and c not in req_cu[r]
    )
    b = sorted(
        f"{r} lista {c}"
        for r, cs in req_cu.items()
        for c in cs
        if c in cu_req and r not in cu_req[c]
    )
    obs: list[str] = []
    if a:
        obs.append(
            f"{len(a)} cita(s) de requisito sin reciprocidad en «CU Asociados»: {_lista(a, 8)}"
        )
    if b:
        obs.append(
            f"{len(b)} caso(s) de uso listado(s) por un requisito que no lo cita: {_lista(b, 8)}"
        )
    return obs


def revisar_operaciones(
    contratos: list[Contrato], cus: dict[str, CasoDeUso], dss_por_cu, dss_sin_cu
) -> list[str]:
    """Contratos contra `dss/DSS.md`, **por nombre de operación** y por caso de uso.

    Una operación se vincula con su contrato por el nombre y nunca por un número. Un contrato
    pertenece a los casos de uso que nombra en sus Referencias Cruzadas; el DSS de cada uno de
    ellos debería mostrar su operación, y cada operación de un DSS debería tener un contrato que
    nombre a ese caso de uso.

    Informa y no corrige. Las diferencias van a `docs/DEUDA.md`.
    """
    obs: list[str] = []
    por_nombre: dict[str, list[Contrato]] = {}
    for co in contratos:
        n = nombre_de_operacion(co.operacion)
        if n:
            por_nombre.setdefault(n, []).append(co)

    con_ficha = sorted(c for c, cu in cus.items() if cu.ficha)
    sin_apartado = [c for c in con_ficha if c not in dss_por_cu]
    if sin_apartado:
        obs.append(
            f"{len(sin_apartado)} caso(s) de uso sin apartado en dss/DSS.md: {_lista(sin_apartado)}"
        )
    huerfanos = sorted(c for c in dss_por_cu if c not in con_ficha)
    if huerfanos:
        obs.append(
            f"{len(huerfanos)} apartado(s) de dss/DSS.md sin ficha en el documento: "
            f"{_lista(huerfanos)}"
        )
    vacios = sorted(c for c, ops in dss_por_cu.items() if not ops and c in con_ficha)
    if vacios:
        obs.append(
            f"{len(vacios)} apartado(s) de dss/DSS.md sin eventos del sistema: {_lista(vacios)}"
        )

    en_dss = {n for ops in dss_por_cu.values() for n in ops} | set(dss_sin_cu)
    sin_contrato = sorted(en_dss - set(por_nombre))
    if sin_contrato:
        obs.append(
            f"{len(sin_contrato)} operación(es) de un DSS sin ningún contrato: "
            f"{_lista(sin_contrato)}"
        )
    sin_dss = sorted(
        f"{n} ({', '.join(c.codigo for c in cos)})"
        for n, cos in por_nombre.items()
        if n not in en_dss
    )
    if sin_dss:
        obs.append(
            f"{len(sin_dss)} contrato(s) cuya operación no aparece en ningún DSS: {_lista(sin_dss)}"
        )

    # por caso de uso
    desde_contratos: dict[str, set[str]] = {}
    for co in contratos:
        n = nombre_de_operacion(co.operacion)
        for c in cus_del_contrato(co):
            desde_contratos.setdefault(c, set()).add(n)
    a, b = [], []
    for c in con_ficha:
        if c not in dss_por_cu:
            continue
        en_su_dss = set(dss_por_cu[c])
        propias = desde_contratos.get(c, set())
        for n in sorted(en_su_dss - propias):
            if n in por_nombre:  # las que no tienen contrato ya se informaron arriba
                a.append(f"{c} · {n} ({', '.join(x.codigo for x in por_nombre[n])})")
        for n in sorted(propias - en_su_dss):
            b.append(f"{c} · {n}")
    if a:
        obs.append(
            f"{len(a)} operación(es) del DSS de un caso de uso cuyo contrato no lo nombra "
            "en Referencias Cruzadas:"
        )
        obs += [f"    {x}" for x in a]
    if b:
        obs.append(
            f"{len(b)} operación(es) cuyo contrato nombra un caso de uso cuyo DSS no la muestra. "
            "Es informativo: suele ser un contrato que cita el caso de uso como contexto (una "
            "consulta previa, una invocación). Sólo es deuda si la operación debería estar en "
            "ese DSS:"
        )
        obs += [f"    {x}" for x in b]

    repetidos = sorted(n for n, cos in por_nombre.items() if len(cos) > 1)
    if repetidos:
        obs.append(
            f"{len(repetidos)} nombre(s) de operación con más de un contrato: "
            + "; ".join(f"{n} → {', '.join(c.codigo for c in por_nombre[n])}" for n in repetidos)
        )
    return obs


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
    p.add_argument(
        "--estricto",
        action="store_true",
        help="sale con código 1 si hubo observaciones de estructura o de referencias",
    )
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

    # --- DSS, que mantiene el responsable ---
    ruta_dss = args.salida / "dss" / "DSS.md"
    dss_por_cu, dss_sin_cu = leer_dss(ruta_dss)

    # --- índice ---
    lineas = [
        "# Índice de casos de uso\n",
        "Punto de entrada. Ubicá el caso de uso y abrí sus cuatro fuentes: la ficha en `cu/`, "
        "su apartado en `dss/DSS.md` (encabezado `### CU-MOD-AAA`), sus contratos en "
        "`contratos/` y el modelo de dominio en las entidades que toca.\n",
        "Los contratos se archivan por sus Referencias Cruzadas. Los que nombran casos de "
        "uso de más de un módulo viven en `contratos/00-transversales.md`.\n",
        "El estado de construcción **no está acá**: vive en `docs/ESTADO.md`.\n",
        "\n| Caso de uso | Nombre | Módulo | Ficha | DSS | Contratos |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for num, mod in sorted(modulos.items()):
        arch = archivos_por_modulo[num]
        for cod in mod.cus:
            cu = cus[cod]
            dss_celda = f"`dss/DSS.md` § {cod}" if cod in dss_por_cu else "—"
            lineas.append(
                f"| `{cod}` | {cu.nombre} | {num} {mod.nombre} "
                f"| `cu/{arch}` | {dss_celda} | `contratos/{arch}` |"
            )
    for cod, cu in sorted(cus.items()):
        if not cu.ficha:
            lineas.append(f"| `{cod}` | {cu.nombre_tarjeta} | — | — | — | — |")
    emitir("INDICE.md", "\n".join(lineas))

    # --- verificación --------------------------------------------------- #
    def seccion(titulo: str, avisos: list[str]) -> int:
        print(f"\n{titulo}")
        for aviso in avisos:
            print(f"  · {aviso}" if not aviso.startswith("    ") else f"  {aviso}")
        if not avisos:
            print("  Sin observaciones.")
        return sum(1 for x in avisos if not x.startswith("    "))

    estructura = revisar_casos_de_uso(cus)
    vacios = [f"{m.numero} {m.nombre}" for m in modulos.values() if not m.cus]
    if vacios:
        estructura.append(f"{len(vacios)} módulo(s) sin fichas: {', '.join(vacios)}")
    faltantes = [n for grupo in CAPITULOS.values() for n in grupo if n not in capitulos]
    if faltantes:
        estructura.append(f"capítulo(s) esperados y no encontrados: {', '.join(faltantes)}")
    estructura += revisar_contratos(contratos)
    # el chequeo que faltaba el 2026-09-14
    if mal_archivados:
        estructura.append(
            f"{len(mal_archivados)} contrato(s) archivado(s) donde ninguno de sus "
            "casos de uso vive:"
        )
        estructura += [f"    {aviso}" for aviso in mal_archivados]

    problemas = seccion("Estructura del documento", estructura)
    problemas += seccion("Referencias en el texto", revisar_referencias(bloques, cus))
    problemas += seccion(
        "Trazabilidad casos de uso ↔ requisitos", revisar_trazabilidad(bloques, cus)
    )

    transversales = por_archivo.get(ARCHIVO_TRANSVERSAL, [])
    print(f"\n  ({len(transversales)} contrato(s) transversal(es) en {ARCHIVO_TRANSVERSAL})")

    print("\nOperaciones: contratos ↔ dss/DSS.md (por nombre, no por número)")
    if not ruta_dss.is_file():
        print(f"  · no se encontró {ruta_dss}; no se puede comparar.")
    else:
        con_dss = sum(1 for c in dss_por_cu if c in cus and cus[c].ficha)
        print(f"  Contratos: {len(contratos)}  ·  Casos de uso con apartado en el DSS: {con_dss}")
        avisos = revisar_operaciones(contratos, cus, dss_por_cu, dss_sin_cu)
        for aviso in avisos:
            print(f"  · {aviso}" if not aviso.startswith("    ") else f"  {aviso}")
        if not avisos:
            print("  Contratos y DSS coinciden.")
    print("\nEl chequeo informa y no corrige: las diferencias van a docs/DEUDA.md.")

    # --- lo que el responsable mantiene --------------------------------- #
    tocados = comparar_huellas(huella_inicial, huella_de(args.salida))
    print(f"\nArchivos del responsable: {len(huella_inicial)} protegido(s)")
    if tocados:
        print("  ERROR: la corrida tocó archivos que no le pertenecen:", file=sys.stderr)
        for aviso in tocados:
            print(f"    · {aviso}", file=sys.stderr)
        return 2
    print("  Ninguno desapareció ni cambió.")
    if args.estricto and problemas:
        print(
            f"\n--estricto: {problemas} observación(es) de estructura o referencias.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
