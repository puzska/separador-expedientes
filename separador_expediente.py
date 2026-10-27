#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
separador_expediente.py
=======================

Separa un PDF de expediente digital en un PDF por trámite y genera un índice
CSV/JSON. Funciona con cualquier expediente, no solo con un formato o juzgado.

El script puede:

1. Detectar los trámites automáticamente desde los marcadores/bookmarks.
2. Elegir el nivel de bookmarks más representativo (índices planos o anidados).
3. Agrupar por fecha y hora, por día o por bookmark.
4. Si no hay bookmarks, intentar detectar inicios de documento por el texto.
5. Usar un "mapa" manual (JSON o CSV) con los cortes exactos de página.
6. Generar un mapa borrador para revisarlo y ajustarlo.

Pensado para usarse solo o para importarlo desde otro programa:

    from separador_expediente import detectar_tramites, dividir_expediente

    tramites = detectar_tramites("expediente.pdf")
    resultado = dividir_expediente("expediente.pdf", "salida", tramites)

Requisitos:
    - Python 3.9+
    - pypdf (pip install pypdf) o PyMuPDF (pip install pymupdf)

El script detecta cuál de las dos librerías está disponible. Si están las dos,
usa pypdf por defecto. También se puede forzar con --backend.

Las páginas siempre son 1-based e inclusivas: "1-3" son las páginas 1, 2 y 3.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

__version__ = "2.0.0"

__all__ = [
    "Tramite",
    "Marcador",
    "ErrorSeparador",
    "SinMarcadoresError",
    "MapaInvalidoError",
    "leer_marcadores",
    "detectar_tramites",
    "cargar_mapa",
    "guardar_mapa",
    "validar_tramites",
    "dividir_expediente",
    "escribir_indices",
    "verificar_salida",
    "slug",
]


# ---------------------------------------------------------------------------
# Errores
# ---------------------------------------------------------------------------


class ErrorSeparador(Exception):
    """Error controlado del separador de expedientes."""


class SinMarcadoresError(ErrorSeparador):
    """El PDF no tiene marcadores/bookmarks utilizables."""


class MapaInvalidoError(ErrorSeparador):
    """El mapa de trámites tiene un formato o contenido inválido."""


# ---------------------------------------------------------------------------
# Modelo de datos
# ---------------------------------------------------------------------------


@dataclass
class Tramite:
    """Un trámite o bloque de páginas del expediente.

    Las páginas son 1-based e inclusivas.
    """

    nombre: str
    pagina_inicio: int
    pagina_fin: int
    categoria: str = "Sin clasificar"
    archivo: str = ""
    fecha: str = ""
    hora: str = ""

    def __post_init__(self) -> None:
        self.pagina_inicio = int(self.pagina_inicio)
        self.pagina_fin = int(self.pagina_fin)
        self.nombre = (self.nombre or "").strip()
        self.categoria = (self.categoria or "Sin clasificar").strip()
        self.fecha = (self.fecha or "").strip()
        self.hora = (self.hora or "").strip()
        if self.archivo:
            self.archivo = nombre_archivo_seguro(self.archivo)
        if not self.nombre and self.archivo:
            self.nombre = nombre_desde_archivo(self.archivo)

    @property
    def paginas(self) -> str:
        return f"{self.pagina_inicio}-{self.pagina_fin}"

    @property
    def cantidad_paginas(self) -> int:
        return self.pagina_fin - self.pagina_inicio + 1

    def to_dict(self) -> dict[str, Any]:
        """Formato compatible con INDICE_TRAMITES.json."""
        return {
            "archivo": self.archivo,
            "categoria": self.categoria,
            "paginas": self.paginas,
            "cant": self.cantidad_paginas,
        }

    def to_mapa_dict(self, indice: int) -> dict[str, Any]:
        """Formato más completo para el mapa editable."""
        fila: dict[str, Any] = {
            "archivo": self.archivo or f"{indice:02d}_{slug(self.nombre)}.pdf",
            "nombre": self.nombre,
            "categoria": self.categoria,
            "paginas": self.paginas,
            "cant": self.cantidad_paginas,
        }
        if self.fecha:
            fila["fecha"] = self.fecha
        if self.hora:
            fila["hora"] = self.hora
        return fila


@dataclass
class Marcador:
    """Una entrada del índice/bookmark del PDF."""

    nivel: int
    titulo: str
    pagina: int
    fecha: str = ""
    hora: str = ""
    titulo_limpio: str = ""


# ---------------------------------------------------------------------------
# Utilidades de texto
# ---------------------------------------------------------------------------


def sin_acentos(texto: str) -> str:
    """Devuelve el texto sin tildes/diacríticos (mantiene eñes como n)."""
    normalizado = unicodedata.normalize("NFKD", texto or "")
    return "".join(c for c in normalizado if not unicodedata.combining(c))


def slug(texto: str, max_len: int = 90) -> str:
    """Convierte un título en un nombre de archivo seguro y legible."""
    base = sin_acentos(texto or "").strip()
    base = re.sub(r"[^A-Za-z0-9]+", "_", base).strip("_")
    if not base:
        base = "tramite"
    if len(base) > max_len:
        base = base[:max_len].rstrip("_")
    return base or "tramite"


def nombre_desde_archivo(archivo: str) -> str:
    """Deriva un nombre legible desde '01_Mi_Tramite.pdf'."""
    stem = Path(str(archivo)).stem
    stem = re.sub(r"^\d+[_\-\s]+", "", stem)
    return stem.replace("_", " ").strip()


def nombre_archivo_seguro(nombre: str) -> str:
    """Quita rutas y caracteres inválidos de Windows; garantiza extensión .pdf."""
    nombre = str(nombre or "").strip().replace("\\", "/")
    nombre = nombre.split("/")[-1]
    nombre = re.sub(r'[<>:"|?*\x00-\x1f]', "_", nombre)
    nombre = nombre.strip(" .")
    if not nombre:
        nombre = "tramite.pdf"
    if not nombre.lower().endswith(".pdf"):
        nombre += ".pdf"
    reservados = {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{i}" for i in range(1, 10)),
        *(f"LPT{i}" for i in range(1, 10)),
    }
    if Path(nombre).stem.upper() in reservados:
        nombre = "_" + nombre
    return nombre


def limpiar_titulo(titulo: str) -> str:
    """Quita fechas, metadatos de adjuntos y datos del profesional."""
    texto = re.sub(r"\s+", " ", titulo or "").strip()

    # Metadatos que agrega el sistema de gestión judicial al final del título.
    texto = re.sub(
        r"\s*[-–—]\s*Esc\.?\+?\.?\s*\d*\s*adjuntos?\.?.*$",
        "",
        texto,
        flags=re.IGNORECASE,
    )
    texto = re.sub(r"\s*[-–—]\s*Dr/?a\.?\s+.*$", "", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\s*M\.P\.?:?\s*\d+\s*$", "", texto, flags=re.IGNORECASE)

    # Prefijos de tipo de documento que no aportan al nombre del trámite.
    texto = re.sub(
        r"^\s*(?:DOCUMENTO|ESCRITO|PRESENTACI[OÓ]N|PRESENTACION|ADJUNTO|ANEXO|"
        r"ARCHIVO)\s*[-–—:|]\s*",
        "",
        texto,
        flags=re.IGNORECASE,
    )
    texto = re.sub(r"^[\s\-–—:|]+", "", texto)
    texto = re.sub(r"[\s\-–—:|]+$", "", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    if texto and texto[0].islower():
        texto = texto[0].upper() + texto[1:]
    return texto


# Formatos de fecha vistos en distintos sistemas de gestión:
# 04/12/2024, 04-12-2024, 04.12.2024, 2024-12-04, 2024/12/04.
_FECHA_PATRON = (
    r"(?:\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|\d{4}[./-]\d{1,2}[./-]\d{1,2})"
)
_HORA_PATRON = r"\d{1,2}:\d{2}(?::\d{2})?"

_RE_FECHA_INICIO = re.compile(
    rf"^\s*[\[\(]?\s*(?P<fecha>{_FECHA_PATRON})"
    rf"(?:\s*[T]?\s*(?:,|a\s+las?)?\s*(?P<hora>{_HORA_PATRON}))?"
    rf"\s*[\]\)]?\s*(?:[-–—:|]\s*)?(?P<titulo>.*)$",
    re.IGNORECASE,
)
_RE_FECHA_FIN = re.compile(
    rf"^(?P<titulo>.+?)\s*(?:[-–—|]\s*|\(\s*|\[\s*)"
    rf"(?P<fecha>{_FECHA_PATRON})"
    rf"(?:\s*(?:,|a\s+las?)?\s*(?P<hora>{_HORA_PATRON}))?"
    rf"\s*[\]\)]?\s*$",
    re.IGNORECASE,
)
_RE_FECHA_SUELTA = re.compile(
    rf"^(?P<titulo>.*\S)\s+(?P<fecha>{_FECHA_PATRON})"
    rf"(?:\s+(?P<hora>{_HORA_PATRON}))?\s*$",
    re.IGNORECASE,
)

# Encabezados internos que no son trámites cuando el PDF no trae fechas.
_RE_SECCION = re.compile(
    r"^\s*(CONSIDERANDO|RESUELVO|RESUELVE|RESULTA|RESULTANDO|"
    r"COSTAS( Y HONORARIOS)?|AUTOS Y VISTOS|VISTOS|FUNDAMENTOS|DECIDE|"
    r"NOTIFIQUESE|FALLO)\s*:?\s*$",
    re.IGNORECASE,
)


def _normalizar_fecha(fecha: str) -> str:
    """Normaliza la fecha a DD/MM/AAAA para poder comparar formatos distintos."""
    limpia = re.sub(r"\s+", "", fecha or "").replace(".", "/").replace("-", "/")
    partes = limpia.split("/")
    if len(partes) != 3:
        return limpia
    a, b, c = partes
    if len(a) == 4:
        anio, mes, dia = a, b, c
    else:
        dia, mes, anio = a, b, c
    if len(anio) == 2:
        anio = "20" + anio
    try:
        return f"{int(dia):02d}/{int(mes):02d}/{anio}"
    except ValueError:
        return limpia


def _normalizar_hora(hora: str) -> str:
    """Normaliza la hora a HH:MM:SS para comparar 11:42 con 11:42:00."""
    partes = (hora or "").strip().split(":")
    try:
        numeros = [int(p) for p in partes]
    except ValueError:
        return (hora or "").strip()
    if len(numeros) == 2:
        return f"{numeros[0]:02d}:{numeros[1]:02d}:00"
    if len(numeros) >= 3:
        return f"{numeros[0]:02d}:{numeros[1]:02d}:{numeros[2]:02d}"
    return (hora or "").strip()


def parsear_fecha_titulo(titulo: str) -> tuple[str, str, str]:
    """Separa la fecha/hora del título y devuelve (fecha, hora, resto).

    Acepta la fecha al inicio (``04/12/2024 19:08:55 - DEMANDA``), al final
    (``DEMANDA - 04/12/2024 19:08``) o entre corchetes/paréntesis.
    """
    original = (titulo or "").strip()
    if not original:
        return "", "", ""

    for patron in (_RE_FECHA_INICIO, _RE_FECHA_FIN, _RE_FECHA_SUELTA):
        coincidencia = patron.match(original)
        if not coincidencia:
            continue
        datos = coincidencia.groupdict()
        resto = (datos.get("titulo") or "").strip()
        resto = re.sub(r"^[\s\-–—:|]+|[\s\-–—:|]+$", "", resto)
        return (
            _normalizar_fecha(datos.get("fecha") or ""),
            _normalizar_hora(datos.get("hora") or ""),
            resto,
        )
    return "", "", original


_REGLAS_CATEGORIA: list[tuple[str, str]] = [
    (
        r"\b(DEMANDA|PROMUEVE (LA )?(EJECUCION|ACCION)|SOLICITA (SE )?EMBARGO)\b",
        "Actuaciones Procesales - Escrito de parte",
    ),
    (
        r"\b(RECURSO|REVOCATORIA|APELACION|AGRAVIOS|QUEJA)\b",
        "Actuaciones Procesales - Recurso",
    ),
    (
        r"\b(PLANILLA|LIQUIDACION|CUOTAS ADEUDADAS)\b",
        "Actuaciones Procesales - Planilla",
    ),
    (
        r"\b(PERICIA|PERITO|CONTADOR|AUDIENCIA|VISTA|TESTIMONIAL)\b",
        "Actuaciones Procesales - Pericia",
    ),
    (
        r"\b(CONTESTA|OPOSICION|TRASLADO)\b",
        "Actuaciones Procesales - Contestacion",
    ),
    (
        r"\b(HONORARIOS|REGULACION)\b",
        "Incidentes Conexos - Regulacion de honorarios",
    ),
    (
        r"\b(EMBARGO|SECUESTRO|MANDAMIENTO|MEDIDA CAUTELAR|INHIBICION|"
        r"SUBASTA|SUPLANTACION|SUSTITUCION)\b",
        "Incidentes Conexos - Medida cautelar",
    ),
    (
        r"^\s*(LIBRAR|AUTORIZAR|ORDENAR|PROVEER|PROVIDENCIA|PROVEIDO|"
        r"DAR CURSO|INTIMAR|TENER|PREVIO|RESUELVE|ADVERTIDO|RECAUDO|"
        r"SE LIBRA|PRACTIQUE|NO LIBRAR)\b",
        "Actuaciones Procesales - Resolucion judicial",
    ),
    (
        r"\b(NOTA DE SECRETARIA|SE ABRE CUENTA)\b",
        "Actuaciones Procesales - Resolucion judicial",
    ),
    (
        r"\b(SENTENCIA|FALLO|AUTOS Y VISTOS|RESUELVO|RESULTA|CONSIDERANDO)\b",
        "Actuaciones Procesales - Resolucion judicial",
    ),
    (r"\b(OFICIO)\b", "Actuaciones Procesales - Oficio"),
    (
        r"\b(NOTIFICA|C[EÉ]D(?:ULA)?|PUBLICACION|NOTIFICACION|"
        r"CONSTANCIA DE ENVIO|DILIGENCIAD[OA])\b",
        "Actuaciones Procesales - Notificacion",
    ),
    (
        r"\b(HABILITACION|PROPONE|CAPTURA|SE PRESENTA)\b",
        "Actuaciones Procesales - Escrito de parte",
    ),
    (
        r"\b(ACOMPA\w*|AGREGAR\w*|ACREDITA\w*|CONST\w*|DOCUMENTO\w*|"
        r"RENUNCIA\w*|COMUNICA\w*|PRESTA CONFORMIDAD|ACTIVA TRAMITE|"
        r"TOMA INTERVENCION)\b",
        "Actuaciones Procesales - Escrito de parte",
    ),
]


def categorizar(titulo: str) -> str:
    """Asigna una categoría aproximada según palabras clave del título."""
    texto = sin_acentos(titulo or "").upper()
    for patron, categoria in _REGLAS_CATEGORIA:
        if re.search(patron, texto):
            return categoria
    return "Sin clasificar"


# ---------------------------------------------------------------------------
# Detección por texto (para PDFs sin bookmarks)
# ---------------------------------------------------------------------------

_RE_SOLO_NUMERO = re.compile(r"^\s*\d{1,4}\s*$")
_RE_ANIO = re.compile(
    r'^\s*[“”"\'«]?\s*\d{4}\s*[-–—]\s*(?:A[ÑN]O|ANIO)\b',
    re.IGNORECASE,
)
_RE_ENCABEZADO_JUDICIAL = re.compile(
    r"^\s*(?:PODER JUDICIAL|JUZGADO|TRIBUNAL|C[AÁ]MARA|SECRETAR[IÍ]A|"
    r"EXPEDIENTE|EXPTE|FOJA)\b",
    re.IGNORECASE,
)
_RE_ENCABEZADO_TEXTO = re.compile(
    r"^\s*(?:DEMANDA|CONTESTA(?:CI[OÓ]N)?|SENTENCIA|PROVIDENCIA|PROVEIDO|"
    r"OFICIO|O\s*F\s*I\s*C\s*I\s*O|ACTA|PERICIA|LIQUIDACI[OÓ]N|PLANILLA|"
    r"PROMUEVE|SOLICITA|ACOMPA[NÑ]A|SE PRESENTA|CONSTITUYE|DESIGNA|IMPUGNA|"
    r"RECURSO|APELACI[OÓ]N|MEMORIAL|ESCRITO|CAR[AÁ]TULA|INFORME|DICTAMEN|"
    r"RESOLUCI[OÓ]N|DECRETO|NOTIFICACI[OÓ]N|C[EÉ]DULA|MANDAMIENTO|EMBARGO|"
    r"SECUESTRO|SUBASTA|RENUNCIA|COMUNICA|PRESTA|"
    r"TOMA(?:R)?\s+INTERVENCI[OÓ]N|AGREGA(?:R)?|ACREDITA|VISTA|TRASLADO|"
    r"EXHIBICI[OÓ]N|NOTA\s+DE\s+SECRETAR[IÍ]A|TR[AÁ]MITE|ACTUACI[OÓ]N)\b",
    re.IGNORECASE,
)
_RE_FECHA_JUDICIAL = re.compile(
    r"^\s*(?:[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+,\s*)?"
    r"(?:\d{1,2}\s+de\s+[a-záéíóúñ]+\s+de\s+\d{2,4}"
    r"|\d{1,2}[./-]\d{1,2}[./-]\d{2,4})\b",
    re.IGNORECASE,
)
# Casos con lugar y fecha incompleta, típicos de oficios:
# "Ciudad Ficticia, Provincia ........ de Junio de 2.025".
_RE_LUGAR_FECHA = re.compile(
    r"^\s*[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+,\s*"
    r"(?:[A-Za-zÁÉÍÓÚÑáéíóúñ]+\s*)?[.\s]*de\s+"
    r"(?:[a-záéíóúñ]+|\.+)\s+de\s+\d{1,4}\b",
    re.IGNORECASE,
)
_RE_ENCABEZADO_CORRIDO = re.compile(
    r'^\s*(?:PODER JUDICIAL|JUZGADO|TRIBUNAL|C[AÁ]MARA|SECRETAR[IÍ]A|'
    r'EXPEDIENTE|EXPTE|FOJA|[“”"\'«]?\s*\d{4}\s*[-–—]\s*A[ÑN]O)\b',
    re.IGNORECASE,
)


def _lineas_legibles(texto: str, limite: int = 12) -> list[str]:
    """Devuelve las primeras líneas no vacías de una página."""
    lineas: list[str] = []
    for linea in (texto or "").splitlines():
        limpia = re.sub(r"\s+", " ", linea).strip()
        if limpia:
            lineas.append(limpia)
        if len(lineas) >= limite:
            break
    return lineas


def _es_encabezado_corrido(
    linea: str, frecuencia: Counter[str], umbral: int
) -> bool:
    """Detecta encabezados que se repiten en casi todas las páginas."""
    return (
        frecuencia.get(linea, 0) > umbral
        and _RE_ENCABEZADO_CORRIDO.match(linea) is not None
    )


def _titulo_desde_lineas(
    lineas: Sequence[str], frecuencia: Counter[str], umbral: int
) -> str:
    """Elige un título legible para una página que inicia un trámite."""
    for linea in lineas:
        if _RE_SOLO_NUMERO.match(linea):
            continue
        if (
            _RE_ANIO.match(linea)
            or _RE_FECHA_JUDICIAL.match(linea)
            or _RE_LUGAR_FECHA.match(linea)
        ):
            continue
        if _es_encabezado_corrido(linea, frecuencia, umbral):
            continue
        if _RE_ENCABEZADO_JUDICIAL.match(linea):
            continue
        if len(re.findall(r"[A-Za-zÁÉÍÓÚÑáéíóúñ]", linea)) < 3:
            continue
        titulo = limpiar_titulo(linea)
        if not titulo:
            continue
        if len(titulo) > 140:
            titulo = titulo[:137].rstrip() + "..."
        return titulo
    return ""


def _pagina_inicia_tramite(
    lineas: Sequence[str], frecuencia: Counter[str], umbral: int
) -> bool:
    """Heurística conservadora para reconocer el inicio de un documento."""
    if not lineas:
        return False

    utiles = [
        linea for linea in lineas if not _RE_SOLO_NUMERO.match(linea)
    ]
    utiles = [
        linea
        for linea in utiles
        if not _es_encabezado_corrido(linea, frecuencia, umbral)
    ]
    if not utiles:
        return False

    reinicia_en_uno = (
        _RE_SOLO_NUMERO.match(lineas[0]) and lineas[0].strip() == "1"
    )

    for indice, linea in enumerate(utiles[:5]):
        # La fecha y el encabezado judicial son señales fuertes solo cerca del
        # inicio. Más abajo suelen ser parte del cuerpo del documento.
        if indice < 3 and (
            _RE_FECHA_JUDICIAL.match(linea)
            or _RE_LUGAR_FECHA.match(linea)
        ):
            return True
        if indice < 2 and _RE_ENCABEZADO_JUDICIAL.match(linea):
            return True

        if not _RE_ENCABEZADO_TEXTO.match(linea):
            continue
        if indice == 0:
            return True
        if reinicia_en_uno and indice < 3:
            return True

        # Un título después de un encabezado judicial/fecha también inicia
        # documento (por ejemplo: "Juzgado..." + "ACOMPAÑA...").
        previas = utiles[:indice]
        if any(
            _RE_FECHA_JUDICIAL.match(anterior)
            or _RE_LUGAR_FECHA.match(anterior)
            or _RE_ENCABEZADO_JUDICIAL.match(anterior)
            or _RE_ANIO.match(anterior)
            for anterior in previas
        ):
            return True

    return False


def _detectar_por_texto(
    pdf: str | Path,
    *,
    backend: str | None = None,
    incluir_paginas_iniciales: bool = True,
) -> list[Tramite]:
    """Fallback para PDFs sin bookmarks: busca inicios de documento en el texto."""
    motor = _crear_backend(pdf, backend)
    try:
        total_paginas = motor.paginas
        lineas_por_pagina = {
            pagina: _lineas_legibles(motor.texto(pagina), 12)
            for pagina in range(1, total_paginas + 1)
        }
    finally:
        motor.cerrar()

    if total_paginas < 1:
        raise SinMarcadoresError("El PDF no tiene páginas.")
    if not any(lineas_por_pagina.values()):
        raise SinMarcadoresError(
            "El PDF no tiene bookmarks ni texto extraíble (¿es un escaneo?). "
            "Creá un mapa manual JSON/CSV con los cortes de página."
        )

    frecuencia: Counter[str] = Counter()
    for lineas in lineas_por_pagina.values():
        utiles = [
            linea for linea in lineas if not _RE_SOLO_NUMERO.match(linea)
        ]
        if utiles:
            frecuencia[utiles[0]] += 1
    umbral = max(4, int(total_paginas * 0.15))

    inicios: list[tuple[int, str]] = []
    for pagina in range(1, total_paginas + 1):
        lineas = lineas_por_pagina[pagina]
        if _pagina_inicia_tramite(lineas, frecuencia, umbral):
            titulo = _titulo_desde_lineas(lineas, frecuencia, umbral)
            inicios.append((pagina, titulo))

    if not inicios:
        raise SinMarcadoresError(
            "No se pudieron detectar inicios de trámite en el texto del PDF. "
            "Generá un mapa borrador y ajustalo a mano."
        )

    if inicios[0][0] > 1 and incluir_paginas_iniciales:
        inicios.insert(0, (1, "Paginas iniciales"))

    # Quitar duplicados conservando el primero.
    vistos: set[int] = set()
    inicios_unicos: list[tuple[int, str]] = []
    for pagina, titulo in inicios:
        if pagina in vistos:
            continue
        vistos.add(pagina)
        inicios_unicos.append((pagina, titulo))

    tramites: list[Tramite] = []
    for indice, (inicio, titulo) in enumerate(inicios_unicos):
        fin = (
            inicios_unicos[indice + 1][0] - 1
            if indice + 1 < len(inicios_unicos)
            else total_paginas
        )
        if fin < inicio:
            continue
        nombre = (titulo or f"Pagina {inicio}").strip()
        tramites.append(
            Tramite(
                nombre=nombre,
                pagina_inicio=inicio,
                pagina_fin=fin,
                categoria=categorizar(nombre),
            )
        )

    if not tramites:
        raise SinMarcadoresError("No se pudo determinar ningún trámite por texto.")
    return tramites


# ---------------------------------------------------------------------------
# Backends de PDF (pypdf o PyMuPDF)
# ---------------------------------------------------------------------------


class _Backend:
    paginas: int

    def marcadores(self) -> list[tuple[int, str, int]]:
        raise NotImplementedError

    def texto(self, pagina: int) -> str:
        raise NotImplementedError

    def guardar_rango(self, inicio: int, fin: int, destino: Path) -> None:
        raise NotImplementedError

    def cerrar(self) -> None:
        pass


class _BackendPypdf(_Backend):
    def __init__(self, ruta: Path) -> None:
        from pypdf import PdfReader  # import local para permitir el fallback

        self._reader = PdfReader(str(ruta))
        if self._reader.is_encrypted:
            raise ErrorSeparador(
                "El PDF está protegido con contraseña; no se puede separar."
            )
        self.paginas = len(self._reader.pages)

    def marcadores(self) -> list[tuple[int, str, int]]:
        resultado: list[tuple[int, str, int]] = []
        outline = getattr(self._reader, "outline", None) or []

        def recorrer(items: Iterable[Any], nivel: int) -> None:
            for item in items:
                if isinstance(item, list):
                    recorrer(item, nivel + 1)
                    continue
                try:
                    pagina = self._reader.get_destination_page_number(item) + 1
                except Exception:
                    continue
                titulo = str(getattr(item, "title", "") or "")
                if pagina >= 1:
                    resultado.append((nivel, titulo, pagina))

        recorrer(outline, 1)
        return resultado

    def texto(self, pagina: int) -> str:
        return self._reader.pages[pagina - 1].extract_text() or ""

    def guardar_rango(self, inicio: int, fin: int, destino: Path) -> None:
        from pypdf import PdfWriter

        writer = PdfWriter()
        for indice in range(inicio - 1, fin):
            writer.add_page(self._reader.pages[indice])
        writer.add_metadata({"/Title": destino.stem})
        with open(destino, "wb") as archivo:
            writer.write(archivo)


class _BackendPyMuPDF(_Backend):
    def __init__(self, ruta: Path) -> None:
        try:
            import pymupdf as fitz
        except ImportError:  # versiones antiguas
            import fitz  # type: ignore

        self._fitz = fitz
        self._doc = fitz.open(str(ruta))
        self.paginas = len(self._doc)

    def marcadores(self) -> list[tuple[int, str, int]]:
        toc = self._doc.get_toc(simple=True) or []
        return [(int(nivel), str(titulo), int(pagina)) for nivel, titulo, pagina in toc if pagina]

    def texto(self, pagina: int) -> str:
        return self._doc[pagina - 1].get_text("text") or ""

    def guardar_rango(self, inicio: int, fin: int, destino: Path) -> None:
        nuevo = self._fitz.open()
        try:
            nuevo.insert_pdf(self._doc, from_page=inicio - 1, to_page=fin - 1)
            nuevo.save(str(destino), garbage=3, deflate=True)
        finally:
            nuevo.close()

    def cerrar(self) -> None:
        self._doc.close()


def _crear_backend(ruta: str | Path, backend: str | None = None) -> _Backend:
    ruta = Path(ruta)
    if backend == "pypdf":
        try:
            return _BackendPypdf(ruta)
        except ImportError as exc:
            raise ErrorSeparador(
                "pypdf no está instalado. Ejecutá: pip install pypdf"
            ) from exc
    if backend == "pymupdf":
        try:
            return _BackendPyMuPDF(ruta)
        except ImportError as exc:
            raise ErrorSeparador(
                "PyMuPDF no está instalado. Ejecutá: pip install pymupdf"
            ) from exc
    if backend is not None:
        raise ErrorSeparador(f"Backend desconocido: {backend!r}")

    try:
        return _BackendPypdf(ruta)
    except ImportError:
        pass
    try:
        return _BackendPyMuPDF(ruta)
    except ImportError as exc:
        raise ErrorSeparador(
            "No hay una librería de PDF instalada. "
            "Ejecutá: pip install pypdf   (o: pip install pymupdf)"
        ) from exc

# ---------------------------------------------------------------------------
# Lectura de marcadores y detección de trámites
# ---------------------------------------------------------------------------


def _leer_crudos(
    pdf: str | Path, backend: str | None = None
) -> tuple[list[tuple[int, str, int]], int]:
    """Lee los bookmarks crudos y el total de páginas.

    Si pypdf abre el PDF pero no puede leer el índice, prueba con PyMuPDF
    (cuando está instalado) antes de darlo por vacío.
    """
    motor = _crear_backend(pdf, backend)
    es_pypdf = isinstance(motor, _BackendPypdf)
    try:
        total_paginas = motor.paginas
        crudos = motor.marcadores()
    finally:
        motor.cerrar()

    if not crudos and backend is None:
        alternativo = "pymupdf" if es_pypdf else "pypdf"
        try:
            motor_alternativo = _crear_backend(pdf, alternativo)
            try:
                total_paginas = motor_alternativo.paginas
                crudos = motor_alternativo.marcadores()
            finally:
                motor_alternativo.cerrar()
        except (ImportError, ErrorSeparador):
            pass

    return crudos, total_paginas


def _marcadores_desde_crudos(
    crudos: Iterable[tuple[int, str, int]],
) -> list[Marcador]:
    marcadores: list[Marcador] = []
    for nivel, titulo, pagina in crudos:
        fecha, hora, resto = parsear_fecha_titulo(titulo)
        marcadores.append(
            Marcador(
                nivel=int(nivel),
                titulo=titulo,
                pagina=int(pagina),
                fecha=fecha,
                hora=hora,
                titulo_limpio=limpiar_titulo(resto),
            )
        )
    return marcadores


def leer_marcadores(
    pdf: str | Path, *, backend: str | None = None
) -> list[Marcador]:
    """Lee el índice/bookmarks del PDF y devuelve una lista de Marcador."""
    crudos, _ = _leer_crudos(pdf, backend)
    return _marcadores_desde_crudos(crudos)


def _sin_secciones(marcadores: Sequence[Marcador]) -> list[Marcador]:
    utiles = [
        m
        for m in marcadores
        if not _RE_SECCION.match((m.titulo_limpio or m.titulo).strip())
    ]
    return utiles or list(marcadores)


def _elegir_candidatos(
    marcadores: Sequence[Marcador],
    nivel: int | None,
    *,
    incluir_sin_fecha: bool = True,
) -> list[Marcador]:
    """Elige el nivel de bookmarks que mejor representa los trámites.

    No todos los expedientes exportan los documentos en el nivel 1. Algunos
    usan un único nodo raíz ("Expediente") y cuelgan los documentos del nivel 2.
    Por eso se elige el nivel con más entradas fechadas; si no hay fechas, el
    nivel más superficial que tenga al menos dos entradas útiles.
    """
    if nivel is not None:
        candidatos = [m for m in marcadores if m.nivel == nivel]
        if not candidatos:
            raise SinMarcadoresError(
                f"El PDF no tiene marcadores de nivel {nivel}."
            )
        candidatos = _sin_secciones(candidatos)
        if not incluir_sin_fecha:
            con_fecha = [m for m in candidatos if m.fecha]
            if con_fecha:
                candidatos = con_fecha
        return candidatos

    por_nivel: dict[int, list[Marcador]] = {}
    for marcador in marcadores:
        por_nivel.setdefault(marcador.nivel, []).append(marcador)
    if not por_nivel:
        raise SinMarcadoresError("El PDF no tiene marcadores/bookmarks.")

    con_fecha = {
        n: [m for m in grupo if m.fecha] for n, grupo in por_nivel.items()
    }
    niveles_con_fecha = [n for n, grupo in con_fecha.items() if grupo]

    if niveles_con_fecha:
        # Más entradas fechadas = nivel más representativo. En empate, el más
        # superficial (el de menor número).
        nivel_elegido = max(
            niveles_con_fecha, key=lambda n: (len(con_fecha[n]), -n)
        )
    else:
        utiles = {
            n: [
                m
                for m in grupo
                if not _RE_SECCION.match(
                    (m.titulo_limpio or m.titulo).strip()
                )
            ]
            for n, grupo in por_nivel.items()
        }
        niveles_utiles = [
            n for n, grupo in utiles.items() if len(grupo) >= 2
        ]
        if niveles_utiles:
            nivel_elegido = min(niveles_utiles)
        else:
            nivel_elegido = max(
                por_nivel, key=lambda n: (len(utiles[n]), -n)
            )
            # Si el nivel 1 es solo un nodo raíz, conviene bajar al nivel de
            # los documentos aunque haya una sola entrada.
            if len(utiles.get(1, [])) <= 1:
                profundos = [
                    n
                    for n in por_nivel
                    if n > 1 and len(utiles[n]) >= len(utiles.get(1, []))
                ]
                if profundos:
                    nivel_elegido = max(
                        profundos, key=lambda n: (len(utiles[n]), n)
                    )

    candidatos = _sin_secciones(por_nivel[nivel_elegido])
    if not incluir_sin_fecha:
        con_fecha_nivel = [m for m in candidatos if m.fecha]
        if con_fecha_nivel:
            candidatos = con_fecha_nivel
    return candidatos


def _mismo_grupo(
    anterior: dict[str, Any],
    marcador: Marcador,
    *,
    agrupar: str,
    fusionar_mismo_instante: bool,
) -> bool:
    if agrupar == "marcador":
        return False
    if not marcador.fecha:
        return False
    if agrupar == "dia":
        return bool(anterior.get("fecha")) and anterior["fecha"] == marcador.fecha
    if not fusionar_mismo_instante:
        return False
    return bool(
        marcador.hora
        and anterior.get("hora") == marcador.hora
        and anterior.get("fecha") == marcador.fecha
    )


def _agrupar_candidatos(
    candidatos: Sequence[Marcador],
    total_paginas: int,
    *,
    agrupar: str,
    fusionar_mismo_instante: bool,
    incluir_paginas_iniciales: bool,
) -> list[dict[str, Any]]:
    grupos: list[dict[str, Any]] = []
    for marcador in sorted(candidatos, key=lambda m: m.pagina):
        if grupos and marcador.pagina == grupos[-1]["inicio"]:
            grupos[-1]["marcadores"].append(marcador)
            if not grupos[-1]["titulo"] and marcador.titulo_limpio:
                grupos[-1]["titulo"] = marcador.titulo_limpio
            continue
        if grupos and _mismo_grupo(
            grupos[-1],
            marcador,
            agrupar=agrupar,
            fusionar_mismo_instante=fusionar_mismo_instante,
        ):
            grupos[-1]["marcadores"].append(marcador)
            continue
        grupos.append(
            {
                "inicio": marcador.pagina,
                "fecha": marcador.fecha,
                "hora": marcador.hora,
                "titulo": marcador.titulo_limpio,
                "marcadores": [marcador],
            }
        )

    for indice, grupo in enumerate(grupos):
        grupo["fin"] = (
            grupos[indice + 1]["inicio"] - 1
            if indice + 1 < len(grupos)
            else total_paginas
        )

    if incluir_paginas_iniciales and grupos and grupos[0]["inicio"] > 1:
        grupos.insert(
            0,
            {
                "inicio": 1,
                "fin": grupos[0]["inicio"] - 1,
                "fecha": "",
                "hora": "",
                "titulo": "Paginas iniciales",
                "marcadores": [],
            },
        )
    return grupos


def _tramites_desde_grupos(
    grupos: Sequence[dict[str, Any]],
) -> list[Tramite]:
    tramites: list[Tramite] = []
    for grupo in grupos:
        inicio = int(grupo["inicio"])
        fin = int(grupo["fin"])
        if fin < inicio:
            continue
        nombre = (grupo.get("titulo") or f"Pagina {inicio}").strip()
        tramites.append(
            Tramite(
                nombre=nombre,
                pagina_inicio=inicio,
                pagina_fin=fin,
                categoria=categorizar(nombre),
                fecha=str(grupo.get("fecha") or ""),
                hora=str(grupo.get("hora") or ""),
            )
        )
    if not tramites:
        raise SinMarcadoresError("No se pudo determinar ningún trámite.")
    return tramites


def detectar_tramites(
    pdf: str | Path,
    *,
    nivel: int | None = None,
    fusionar_mismo_instante: bool = True,
    incluir_paginas_iniciales: bool = True,
    backend: str | None = None,
    agrupar: str = "fecha",
    incluir_sin_fecha: bool = True,
    modo: str = "auto",
) -> list[Tramite]:
    """Detecta trámites en un expediente.

    ``modo``:
      - ``auto`` (por defecto): usa bookmarks; si no hay o son insuficientes,
        intenta detectar inicios de documento por texto.
      - ``bookmarks``: solo bookmarks. Falla si el PDF no tiene.
      - ``texto``: solo análisis de texto (útil para PDFs sin bookmarks).

    ``agrupar``:
      - ``fecha``: fusiona bookmarks con la misma fecha y hora (mismo envío).
      - ``dia``: fusiona todos los bookmarks de la misma fecha.
      - ``marcador``: un trámite por bookmark (salvo los que apuntan a la
        misma página, que se fusionan para no generar rangos vacíos).

    ``incluir_sin_fecha`` incluye bookmarks sin fecha como posibles trámites.
    ``incluir_paginas_iniciales`` crea un trámite para las páginas previas al
    primer bookmark.
    """
    if agrupar not in {"fecha", "dia", "marcador"}:
        raise ValueError(
            "agrupar debe ser 'fecha', 'dia' o 'marcador'."
        )
    if modo not in {"auto", "bookmarks", "texto"}:
        raise ValueError("modo debe ser 'auto', 'bookmarks' o 'texto'.")
    if not fusionar_mismo_instante and agrupar == "fecha":
        agrupar = "marcador"

    resultado_bookmarks: list[Tramite] | None = None

    if modo in {"auto", "bookmarks"}:
        crudos, total_paginas = _leer_crudos(pdf, backend)
        if crudos:
            try:
                marcadores = _marcadores_desde_crudos(crudos)
                candidatos = _elegir_candidatos(
                    marcadores,
                    nivel,
                    incluir_sin_fecha=incluir_sin_fecha,
                )
                candidatos = [
                    m for m in candidatos if 1 <= m.pagina <= total_paginas
                ]
                if not candidatos:
                    raise SinMarcadoresError(
                        "Los marcadores del PDF no apuntan a páginas válidas."
                    )
                grupos = _agrupar_candidatos(
                    candidatos,
                    total_paginas,
                    agrupar=agrupar,
                    fusionar_mismo_instante=fusionar_mismo_instante,
                    incluir_paginas_iniciales=incluir_paginas_iniciales,
                )
                resultado_bookmarks = _tramites_desde_grupos(grupos)

                # Un único bookmark en un PDF largo suele ser un índice roto.
                # En modo auto se intenta el fallback por texto.
                if modo == "bookmarks" or len(resultado_bookmarks) >= 2:
                    return resultado_bookmarks
                if total_paginas <= 3:
                    return resultado_bookmarks
            except SinMarcadoresError:
                if modo == "bookmarks" or nivel is not None:
                    raise
        elif modo == "bookmarks":
            raise SinMarcadoresError(
                "El PDF no tiene marcadores/bookmarks utilizables. "
                "Usá modo='texto' o un mapa manual (JSON/CSV)."
            )

    if modo in {"auto", "texto"}:
        try:
            por_texto = _detectar_por_texto(
                pdf,
                backend=backend,
                incluir_paginas_iniciales=incluir_paginas_iniciales,
            )
            if (
                resultado_bookmarks is None
                or len(por_texto) > len(resultado_bookmarks)
            ):
                return por_texto
            return resultado_bookmarks
        except SinMarcadoresError as exc:
            if resultado_bookmarks is not None:
                return resultado_bookmarks
            if modo == "auto":
                raise SinMarcadoresError(
                    "El PDF no tiene bookmarks utilizables y tampoco se "
                    "pudieron detectar inicios de trámite en el texto. "
                    "Generá un mapa borrador y ajustalo a mano."
                ) from exc
            raise

    if resultado_bookmarks is not None:
        return resultado_bookmarks
    raise SinMarcadoresError("No se pudo determinar ningún trámite.")


# ---------------------------------------------------------------------------
# Mapa manual / índice
# ---------------------------------------------------------------------------

_CLAVES = {
    "archivo": ("archivo", "file", "filename", "nombre_archivo"),
    "nombre": ("nombre", "name", "titulo", "title"),
    "categoria": ("categoria", "category", "tipo"),
    "paginas": ("paginas", "pages", "rango", "rango_paginas"),
    "inicio": ("pagina_inicio", "inicio", "page_start", "desde"),
    "fin": ("pagina_fin", "fin", "page_end", "hasta"),
    "cant": ("cant", "cantidad", "cantidad_paginas", "cantidad_de_paginas", "count"),
    "fecha": ("fecha", "date"),
    "hora": ("hora", "time"),
}


def _clave_normalizada(clave: Any) -> str:
    texto = sin_acentos(str(clave or "")).lower()
    return re.sub(r"[^a-z0-9]+", "_", texto).strip("_")


def _normalizar_fila(fila: dict[str, Any]) -> dict[str, Any]:
    normalizada = {_clave_normalizada(k): v for k, v in fila.items() if k is not None}
    resultado: dict[str, Any] = {}
    for destino, alternativas in _CLAVES.items():
        for alternativa in alternativas:
            if alternativa in normalizada:
                resultado[destino] = normalizada[alternativa]
                break
    return resultado


def _texto(valor: Any) -> str:
    if valor is None:
        return ""
    return str(valor).strip()


def _entero(valor: Any) -> int | None:
    if valor is None or valor == "":
        return None
    try:
        return int(float(str(valor).replace(",", ".")))
    except (TypeError, ValueError):
        return None


def _paginas_de_fila(fila: dict[str, Any]) -> tuple[int | None, int | None]:
    valor = fila.get("paginas")
    if valor not in (None, ""):
        if isinstance(valor, (list, tuple)) and len(valor) >= 2:
            return _entero(valor[0]), _entero(valor[1])
        coincidencia = re.match(
            r"^\s*(\d+)\s*(?:-|–|—|a|hasta)\s*(\d+)\s*$",
            str(valor),
            re.IGNORECASE,
        )
        if coincidencia:
            return int(coincidencia.group(1)), int(coincidencia.group(2))
        coincidencia = re.match(r"^\s*(\d+)\s*$", str(valor))
        if coincidencia:
            pagina = int(coincidencia.group(1))
            return pagina, pagina

    inicio = _entero(fila.get("inicio"))
    fin = _entero(fila.get("fin"))
    if inicio is not None and fin is not None:
        return inicio, fin
    return None, None


def _leer_filas(ruta: Path) -> list[dict[str, Any]]:
    if ruta.suffix.lower() == ".json":
        datos = json.loads(ruta.read_text(encoding="utf-8-sig"))
    else:
        with open(ruta, "r", encoding="utf-8-sig", newline="") as archivo:
            muestra = archivo.read(8192)
            archivo.seek(0)
            try:
                dialecto = csv.Sniffer().sniff(muestra, delimiters=",;\t|")
            except csv.Error:
                dialecto = csv.excel
            datos = list(csv.DictReader(archivo, dialect=dialecto))

    if isinstance(datos, dict):
        datos = (
            datos.get("tramites")
            or datos.get("items")
            or datos.get("indice")
            or datos.get("data")
        )
    if not isinstance(datos, list):
        raise MapaInvalidoError(
            "El mapa debe ser una lista de trámites (JSON) o un CSV con encabezados."
        )
    return datos


def cargar_mapa(ruta: str | Path) -> list[Tramite]:
    """Carga un mapa JSON o CSV con los cortes de página.

    Formatos aceptados por fila:
      - {"archivo": "01_....pdf", "nombre": "...", "categoria": "...",
         "paginas": "1-3"}
      - {"nombre": "...", "pagina_inicio": 1, "pagina_fin": 3}
      - {"archivo": "01_....pdf", "categoria": "...", "cant": 3}
        (en este último caso las páginas se calculan en orden desde la 1)
    """
    ruta = Path(ruta)
    if not ruta.exists():
        raise FileNotFoundError(f"No existe el mapa: {ruta}")

    filas = _leer_filas(ruta)
    tramites: list[Tramite] = []
    siguiente_pagina = 1

    for numero, fila_cruda in enumerate(filas, 1):
        if not isinstance(fila_cruda, dict):
            raise MapaInvalidoError(f"Fila {numero}: se esperaba un objeto.")
        fila = _normalizar_fila(fila_cruda)

        archivo = _texto(fila.get("archivo"))
        nombre = _texto(fila.get("nombre"))
        categoria = _texto(fila.get("categoria")) or "Sin clasificar"
        inicio, fin = _paginas_de_fila(fila)

        if inicio is None or fin is None:
            cantidad = _entero(fila.get("cant"))
            if cantidad is None:
                raise MapaInvalidoError(
                    f"Fila {numero}: falta 'paginas' (o 'pagina_inicio'/'pagina_fin', "
                    "o 'cant')."
                )
            inicio = siguiente_pagina
            fin = inicio + cantidad - 1

        if not nombre and archivo:
            nombre = nombre_desde_archivo(archivo)
        if not nombre:
            nombre = f"Tramite {numero}"

        tramites.append(
            Tramite(
                nombre=nombre,
                pagina_inicio=inicio,
                pagina_fin=fin,
                categoria=categoria,
                archivo=archivo,
                fecha=_texto(fila.get("fecha")),
                hora=_texto(fila.get("hora")),
            )
        )
        siguiente_pagina = fin + 1

    if not tramites:
        raise MapaInvalidoError(f"El mapa {ruta} no contiene trámites.")
    return sorted(tramites, key=lambda t: (t.pagina_inicio, t.pagina_fin))


def guardar_mapa(
    tramites: Sequence[Tramite], ruta: str | Path
) -> Path:
    """Guarda un mapa editable en JSON (o CSV si la extensión es .csv)."""
    ruta = Path(ruta)
    filas = [t.to_mapa_dict(indice) for indice, t in enumerate(tramites, 1)]
    ruta.parent.mkdir(parents=True, exist_ok=True)

    if ruta.suffix.lower() == ".csv":
        with open(ruta, "w", encoding="utf-8-sig", newline="") as archivo:
            writer = csv.DictWriter(
                archivo,
                fieldnames=[
                    "archivo",
                    "nombre",
                    "categoria",
                    "paginas",
                    "cant",
                    "fecha",
                    "hora",
                ],
                extrasaction="ignore",
            )
            writer.writeheader()
            writer.writerows(filas)
    else:
        ruta.write_text(
            json.dumps(filas, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return ruta


# ---------------------------------------------------------------------------
# Validación e índices
# ---------------------------------------------------------------------------


def _resumen_rangos(paginas: Sequence[int]) -> str:
    if not paginas:
        return ""
    ordenadas = sorted(set(paginas))
    tramos: list[str] = []
    inicio = anterior = ordenadas[0]
    for pagina in ordenadas[1:]:
        if pagina == anterior + 1:
            anterior = pagina
            continue
        tramos.append(str(inicio) if inicio == anterior else f"{inicio}-{anterior}")
        inicio = anterior = pagina
    tramos.append(str(inicio) if inicio == anterior else f"{inicio}-{anterior}")
    return ", ".join(tramos)


def validar_tramites(
    tramites: Sequence[Tramite],
    total_paginas: int,
    *,
    permitir_huecos: bool = False,
) -> tuple[list[Tramite], list[int]]:
    """Valida rangos y devuelve (trámites ordenados, páginas sin asignar)."""
    if not tramites:
        raise MapaInvalidoError("No hay trámites para dividir.")

    ordenados = sorted(tramites, key=lambda t: (t.pagina_inicio, t.pagina_fin))
    for tramite in ordenados:
        if tramite.pagina_inicio < 1:
            raise MapaInvalidoError(
                f"'{tramite.nombre}': la página inicial debe ser >= 1."
            )
        if tramite.pagina_fin > total_paginas:
            raise MapaInvalidoError(
                f"'{tramite.nombre}': la página final ({tramite.pagina_fin}) "
                f"supera el total del PDF ({total_paginas})."
            )
        if tramite.pagina_inicio > tramite.pagina_fin:
            raise MapaInvalidoError(
                f"'{tramite.nombre}': rango inválido {tramite.paginas}."
            )

    for anterior, siguiente in zip(ordenados, ordenados[1:]):
        if siguiente.pagina_inicio <= anterior.pagina_fin:
            raise MapaInvalidoError(
                "Hay páginas superpuestas entre "
                f"'{anterior.nombre}' ({anterior.paginas}) y "
                f"'{siguiente.nombre}' ({siguiente.paginas})."
            )

    cubiertas: set[int] = set()
    for tramite in ordenados:
        cubiertas.update(range(tramite.pagina_inicio, tramite.pagina_fin + 1))
    faltantes = [p for p in range(1, total_paginas + 1) if p not in cubiertas]

    if faltantes and not permitir_huecos:
        raise MapaInvalidoError(
            f"Hay {len(faltantes)} páginas sin asignar: {_resumen_rangos(faltantes)}. "
            "Corregí el mapa o usá --permitir-huecos."
        )
    return ordenados, faltantes


def escribir_indices(
    salida: str | Path,
    tramites: Sequence[Tramite],
    *,
    nombre_base: str = "INDICE_TRAMITES",
) -> tuple[Path, Path]:
    """Escribe el índice en JSON y CSV. Devuelve (ruta_json, ruta_csv)."""
    salida = Path(salida)
    salida.mkdir(parents=True, exist_ok=True)

    ruta_json = salida / f"{nombre_base}.json"
    ruta_csv = salida / f"{nombre_base}.csv"

    filas = [tramite.to_dict() for tramite in tramites]
    ruta_json.write_text(
        json.dumps(filas, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    with open(ruta_csv, "w", encoding="utf-8-sig", newline="") as archivo:
        archivo.write("Archivo,Categoria,Paginas,Cantidad de paginas\n")
        for tramite in tramites:
            archivo_nombre = str(tramite.archivo).replace('"', '""')
            categoria = str(tramite.categoria).replace('"', '""')
            archivo.write(
                f'"{archivo_nombre}","{categoria}","{tramite.paginas}",'
                f"{tramite.cantidad_paginas}\n"
            )

    return ruta_json, ruta_csv

# ---------------------------------------------------------------------------
# División y verificación
# ---------------------------------------------------------------------------


def _sanear_prefijo(prefijo: str) -> str:
    """Limpia un prefijo para usarlo al inicio de los nombres de archivo."""
    texto = str(prefijo or "").replace("\\", "/").split("/")[-1]
    texto = re.sub(r'[<>:"|?*\x00-\x1f]', "_", texto).strip(" .")
    if texto.lower().endswith(".pdf"):
        texto = texto[:-4].rstrip(" .")
    return texto


def _asignar_nombres(
    tramites: Sequence[Tramite], *, prefijo: str = ""
) -> list[Tramite]:
    """Completa nombres de archivo, aplica un prefijo y evita duplicados."""
    prefijo = _sanear_prefijo(prefijo)
    usados: set[str] = set()
    resultado: list[Tramite] = []
    for indice, tramite in enumerate(tramites, 1):
        if not tramite.archivo:
            tramite.archivo = (
                f"{prefijo}{indice:02d}_{slug(tramite.nombre)}.pdf"
            )
        else:
            tramite.archivo = nombre_archivo_seguro(tramite.archivo)
            if prefijo and not tramite.archivo.lower().startswith(
                prefijo.lower()
            ):
                tramite.archivo = nombre_archivo_seguro(
                    prefijo + tramite.archivo
                )

        candidato = tramite.archivo
        if candidato.lower() in usados:
            stem = Path(candidato).stem
            sufijo = Path(candidato).suffix or ".pdf"
            contador = 2
            while f"{stem}_{contador}{sufijo}".lower() in usados:
                contador += 1
            tramite.archivo = f"{stem}_{contador}{sufijo}"
        usados.add(tramite.archivo.lower())
        resultado.append(tramite)
    return resultado


def dividir_expediente(
    pdf_entrada: str | Path,
    salida: str | Path,
    tramites: Sequence[Tramite] | None = None,
    *,
    mapa: str | Path | None = None,
    escribir_indice: bool = True,
    sobrescribir: bool = False,
    permitir_huecos: bool = False,
    backend: str | None = None,
    progreso: Callable[[int, int, Tramite], None] | None = None,
    nivel: int | None = None,
    agrupar: str = "fecha",
    fusionar_mismo_instante: bool = True,
    incluir_sin_fecha: bool = True,
    incluir_paginas_iniciales: bool = True,
    modo: str = "auto",
    prefijo: str = "",
) -> list[Tramite]:
    """Divide el PDF y devuelve los trámites con su nombre de archivo final.

    Si se pasa `mapa`, se carga desde JSON/CSV y tiene prioridad sobre
    `tramites`. Si no se pasa ni mapa ni trámites, se detectan automáticamente
    (bookmarks y, si hace falta, texto).

    ``prefijo`` se antepone a los nombres de archivo finales, por ejemplo
    ``"0000123_"`` para distinguir expedientes.
    """
    pdf_entrada = Path(pdf_entrada)
    salida = Path(salida)

    if not pdf_entrada.exists():
        raise FileNotFoundError(f"No existe el PDF: {pdf_entrada}")
    if mapa is not None:
        if tramites is not None:
            raise ValueError("Usá 'mapa' o 'tramites', no ambos.")
        tramites = cargar_mapa(mapa)
    elif tramites is None:
        tramites = detectar_tramites(
            pdf_entrada,
            nivel=nivel,
            fusionar_mismo_instante=fusionar_mismo_instante,
            incluir_paginas_iniciales=incluir_paginas_iniciales,
            backend=backend,
            agrupar=agrupar,
            incluir_sin_fecha=incluir_sin_fecha,
            modo=modo,
        )

    motor = _crear_backend(pdf_entrada, backend)
    try:
        total_paginas = motor.paginas
        ordenados, faltantes = validar_tramites(
            list(tramites),
            total_paginas,
            permitir_huecos=permitir_huecos,
        )
        ordenados = _asignar_nombres(ordenados, prefijo=prefijo)

        if not sobrescribir:
            existentes = [
                str(salida / tramite.archivo)
                for tramite in ordenados
                if (salida / tramite.archivo).exists()
            ]
            if existentes:
                listado = "\n  ".join(existentes[:10])
                extra = "" if len(existentes) <= 10 else f"\n  ... y {len(existentes) - 10} más"
                raise FileExistsError(
                    "Ya existen archivos de salida:\n  "
                    f"{listado}{extra}\n"
                    "Usá --sobrescribir para reemplazarlos o elegí otra carpeta."
                )

        salida.mkdir(parents=True, exist_ok=True)
        for indice, tramite in enumerate(ordenados, 1):
            destino = salida / tramite.archivo
            motor.guardar_rango(
                tramite.pagina_inicio,
                tramite.pagina_fin,
                destino,
            )
            if progreso is not None:
                progreso(indice, len(ordenados), tramite)

        if escribir_indice:
            escribir_indices(salida, ordenados)

        if faltantes:
            print(
                "Aviso: quedaron páginas sin asignar: "
                f"{_resumen_rangos(faltantes)}",
                file=sys.stderr,
            )

        return ordenados
    finally:
        motor.cerrar()


def verificar_salida(
    salida: str | Path,
    tramites: Sequence[Tramite],
    *,
    backend: str | None = None,
) -> list[str]:
    """Verifica que cada PDF exista y tenga la cantidad de páginas esperada."""
    salida = Path(salida)
    problemas: list[str] = []
    for tramite in tramites:
        ruta = salida / tramite.archivo
        if not ruta.exists():
            problemas.append(f"Falta el archivo: {tramite.archivo}")
            continue
        try:
            motor = _crear_backend(ruta, backend)
            try:
                paginas = motor.paginas
            finally:
                motor.cerrar()
        except Exception as exc:  # PDF ilegible
            problemas.append(f"{tramite.archivo}: no se pudo leer ({exc})")
            continue
        if paginas != tramite.cantidad_paginas:
            problemas.append(
                f"{tramite.archivo}: tiene {paginas} páginas, "
                f"se esperaban {tramite.cantidad_paginas}."
            )
    return problemas


# ---------------------------------------------------------------------------
# Salida por consola
# ---------------------------------------------------------------------------


def _imprimir_tabla(tramites: Sequence[Tramite]) -> None:
    print(f"{'#':>3}  {'Paginas':<12} {'Cant.':>5}  {'Categoria':<45} Nombre")
    print("-" * 130)
    for indice, tramite in enumerate(tramites, 1):
        categoria = tramite.categoria
        if len(categoria) > 45:
            categoria = categoria[:42] + "..."
        print(
            f"{indice:>3}  {tramite.paginas:<12} "
            f"{tramite.cantidad_paginas:>5}  {categoria:<45} {tramite.nombre}"
        )
    total_paginas = sum(t.cantidad_paginas for t in tramites)
    print("-" * 130)
    print(f"Total: {len(tramites)} trámites, {total_paginas} páginas.")


def _imprimir_marcadores(marcadores: Sequence[Marcador]) -> None:
    print(f"{'Nivel':<6} {'Pag.':>5}  {'Fecha':<10} {'Hora':<8} Titulo")
    print("-" * 120)
    for marcador in marcadores:
        print(
            f"{marcador.nivel:<6} {marcador.pagina:>5}  "
            f"{marcador.fecha:<10} {marcador.hora:<8} {marcador.titulo}"
        )
    print("-" * 120)
    print(f"Total: {len(marcadores)} marcadores.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _nombre_programa() -> str:
    """Nombre a mostrar en la ayuda, según cómo se invocó el programa."""
    nombre = Path(sys.argv[0]).stem
    if nombre.lower() in {"separador-expedientes", "separador_expediente"}:
        return nombre
    return "separador-expedientes"


def _crear_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=_nombre_programa(),
        description=(
            "Separa un PDF de expediente digital en un PDF por trámite y "
            "genera un índice CSV/JSON."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Ejemplos:
  # Ver los trámites detectados desde los marcadores del PDF
  python separador_expediente.py expediente.pdf --listar

  # Separar automáticamente (modo por defecto)
  python separador_expediente.py expediente.pdf -o "TRAMITES SEPARADOS"

  # Agrupar por día o generar un PDF por bookmark
  python separador_expediente.py expediente.pdf -o salida --agrupar dia
  python separador_expediente.py expediente.pdf -o salida --agrupar marcador

  # Forzar detección por texto (PDF sin bookmarks)
  python separador_expediente.py expediente.pdf -o salida --modo texto

  # Separar con un mapa curado (JSON o CSV)
  python separador_expediente.py expediente.pdf -o salida --mapa mapa.json

  # Generar un mapa borrador para editar a mano
  python separador_expediente.py expediente.pdf --generar-mapa mapa.json

  # Anteponer el número de expediente a los archivos
  python separador_expediente.py expediente.pdf -o salida --prefijo "0000123_"

  # Ver todos los marcadores/bookmarks del PDF
  python separador_expediente.py expediente.pdf --marcadores
""",
    )
    parser.add_argument("pdf", help="PDF del expediente digital.")
    parser.add_argument(
        "-o",
        "--salida",
        help="Carpeta donde guardar los PDFs separados y el índice.",
    )
    parser.add_argument(
        "--mapa",
        help="Mapa JSON/CSV con los cortes de página (tiene prioridad sobre --auto).",
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Detección automática (es el modo por defecto; se conserva por compatibilidad).",
    )
    parser.add_argument(
        "--modo",
        choices=("auto", "bookmarks", "texto"),
        default="auto",
        help=(
            "auto: bookmarks y, si faltan, texto (por defecto). "
            "bookmarks: solo índice del PDF. texto: solo análisis de texto."
        ),
    )
    parser.add_argument(
        "--agrupar",
        choices=("fecha", "dia", "marcador"),
        default="fecha",
        help=(
            "fecha: mismo envío (fecha y hora), dia: misma fecha, "
            "marcador: un trámite por bookmark. Por defecto: fecha."
        ),
    )
    parser.add_argument(
        "--solo-con-fecha",
        action="store_true",
        help="Ignorar bookmarks sin fecha (por defecto se incluyen).",
    )
    parser.add_argument(
        "--sin-paginas-iniciales",
        action="store_true",
        help="No crear un trámite para las páginas previas al primer bookmark.",
    )
    parser.add_argument(
        "--prefijo",
        default="",
        help='Prefijo para los archivos de salida, por ejemplo "0000123_".',
    )
    parser.add_argument(
        "--listar",
        action="store_true",
        help="Mostrar los trámites detectados o el mapa, sin dividir.",
    )
    parser.add_argument(
        "--marcadores",
        action="store_true",
        help="Mostrar todos los marcadores/bookmarks del PDF.",
    )
    parser.add_argument(
        "--generar-mapa",
        metavar="ARCHIVO",
        help="Guardar un mapa borrador (JSON o CSV) y salir.",
    )
    parser.add_argument(
        "--nivel",
        type=int,
        default=None,
        help=(
            "Usar solo marcadores de este nivel. Por defecto se elige el nivel "
            "con más entradas fechadas."
        ),
    )
    parser.add_argument(
        "--sin-fusionar",
        action="store_true",
        help="No fusionar marcadores con la misma fecha y hora (equivale a --agrupar marcador).",
    )
    parser.add_argument(
        "--sin-indice",
        action="store_true",
        help="No generar INDICE_TRAMITES.csv/json.",
    )
    parser.add_argument(
        "--sobrescribir",
        action="store_true",
        help="Reemplazar archivos existentes en la carpeta de salida.",
    )
    parser.add_argument(
        "--permitir-huecos",
        action="store_true",
        help="Permitir páginas sin asignar en el mapa.",
    )
    parser.add_argument(
        "--verificar",
        action="store_true",
        help="Verificar los PDFs generados después de dividir.",
    )
    parser.add_argument(
        "--backend",
        choices=("pypdf", "pymupdf"),
        default=None,
        help="Forzar la librería de PDF (por defecto, pypdf si está disponible).",
    )
    parser.add_argument(
        "--silencioso",
        action="store_true",
        help="No mostrar el progreso archivo por archivo.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Mostrar el detalle completo de los errores inesperados.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _crear_parser()
    args = parser.parse_args(argv)

    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    if args.auto and args.mapa:
        parser.error("Usá --auto o --mapa, no ambos.")

    pdf = Path(args.pdf)
    if not pdf.exists():
        print(f"ERROR: no existe el PDF: {pdf}", file=sys.stderr)
        return 2

    def detectar() -> list[Tramite]:
        return detectar_tramites(
            pdf,
            nivel=args.nivel,
            fusionar_mismo_instante=not args.sin_fusionar,
            incluir_paginas_iniciales=not args.sin_paginas_iniciales,
            backend=args.backend,
            agrupar=args.agrupar,
            incluir_sin_fecha=not args.solo_con_fecha,
            modo=args.modo,
        )

    try:
        if args.marcadores:
            _imprimir_marcadores(leer_marcadores(pdf, backend=args.backend))
            return 0

        if args.mapa:
            tramites: list[Tramite] | None = cargar_mapa(args.mapa)
        else:
            tramites = None

        if args.listar:
            if tramites is None:
                tramites = detectar()
            _imprimir_tabla(tramites)
            return 0

        if args.generar_mapa:
            if tramites is None:
                tramites = detectar()
            ruta = guardar_mapa(tramites, args.generar_mapa)
            print(f"Mapa guardado en: {ruta.resolve()} ({len(tramites)} trámites)")
            _imprimir_tabla(tramites)
            return 0

        if not args.salida:
            if tramites is None:
                tramites = detectar()
            _imprimir_tabla(tramites)
            print(
                "\nPara dividir el PDF, indicá una carpeta de salida con -o/--salida."
            )
            print(
                'Ejemplo: python separador_expediente.py expediente.pdf '
                '-o "TRAMITES SEPARADOS"'
            )
            return 0

        def mostrar_progreso(indice: int, total: int, tramite: Tramite) -> None:
            if not args.silencioso:
                print(f"[{indice:>3}/{total}] {tramite.archivo}")

        resultado = dividir_expediente(
            pdf,
            args.salida,
            tramites=tramites,
            escribir_indice=not args.sin_indice,
            sobrescribir=args.sobrescribir,
            permitir_huecos=args.permitir_huecos,
            backend=args.backend,
            progreso=mostrar_progreso,
            nivel=args.nivel,
            agrupar=args.agrupar,
            fusionar_mismo_instante=not args.sin_fusionar,
            incluir_sin_fecha=not args.solo_con_fecha,
            incluir_paginas_iniciales=not args.sin_paginas_iniciales,
            modo=args.modo,
            prefijo=args.prefijo,
        )

        print()
        print(
            f"Listo: {len(resultado)} trámites en {Path(args.salida).resolve()}"
        )
        if not args.sin_indice:
            print(
                f"Índice: {Path(args.salida).resolve() / 'INDICE_TRAMITES.csv'}"
            )
        _imprimir_tabla(resultado)

        if args.verificar:
            problemas = verificar_salida(args.salida, resultado, backend=args.backend)
            if problemas:
                print("\nVerificación con problemas:", file=sys.stderr)
                for problema in problemas:
                    print(f"  - {problema}", file=sys.stderr)
                return 1
            print("\nVerificación OK: todos los PDFs tienen las páginas esperadas.")
        return 0

    except (ErrorSeparador, FileNotFoundError, FileExistsError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001 - CLI amigable
        if args.debug:
            raise
        print(f"ERROR inesperado: {exc}", file=sys.stderr)
        print("Usá --debug para ver el detalle.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
