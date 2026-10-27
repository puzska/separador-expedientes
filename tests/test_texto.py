"""Tests de las utilidades de texto y del modelo de datos."""

from __future__ import annotations

import pytest

import separador_expediente as sep


@pytest.mark.parametrize(
    ("titulo", "esperado"),
    [
        (
            "04/12/2024 19:08:55 - DEMANDA",
            ("04/12/2024", "19:08:55", "DEMANDA"),
        ),
        (
            "2025-02-03 11:42 - PROVIDENCIA",
            ("03/02/2025", "11:42:00", "PROVIDENCIA"),
        ),
        ("DEMANDA - 04.12.2024", ("04/12/2024", "", "DEMANDA")),
        ("[10/03/25 08:00] SENTENCIA", ("10/03/2025", "08:00:00", "SENTENCIA")),
        (
            "04/12/2024 a las 19:08 - OFICIO",
            ("04/12/2024", "19:08:00", "OFICIO"),
        ),
        ("OFICIO (12/03/2025)", ("12/03/2025", "", "OFICIO")),
        ("2024/12/04 7:05 - NOTA", ("04/12/2024", "07:05:00", "NOTA")),
        ("SIN FECHA", ("", "", "SIN FECHA")),
        ("", ("", "", "")),
    ],
)
def test_parsear_fecha_titulo(titulo, esperado):
    assert sep.parsear_fecha_titulo(titulo) == esperado


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("DOCUMENTO - DEMANDA DE ALIMENTOS", "DEMANDA DE ALIMENTOS"),
        ("DEMANDA - Esc. 2 adjuntos - Dr. Ficticio", "DEMANDA"),
        ("DEMANDA - Esc.+.3 adjuntos.- Dra. Ejemplo", "DEMANDA"),
        ("PROVIDENCIA - Dra. Ejemplo", "PROVIDENCIA"),
        ("OFICIO - M.P. 1234", "OFICIO"),
        ("Escrito: DEMANDA", "DEMANDA"),
        ("  hola   mundo  ", "Hola mundo"),
        ("", ""),
    ],
)
def test_limpiar_titulo(entrada, esperado):
    assert sep.limpiar_titulo(entrada) == esperado


@pytest.mark.parametrize(
    ("titulo", "esperado"),
    [
        ("DEMANDA DE ALIMENTOS", "Actuaciones Procesales - Escrito de parte"),
        ("CONTESTA EL TRASLADO", "Actuaciones Procesales - Contestacion"),
        ("SENTENCIA", "Actuaciones Procesales - Resolucion judicial"),
        ("LIBRAR OFICIO", "Actuaciones Procesales - Resolucion judicial"),
        ("OFICIO DILIGENCIADO", "Actuaciones Procesales - Oficio"),
        ("CEDULA DILIGENCIADA", "Actuaciones Procesales - Notificacion"),
        ("NOTA DE SECRETARIA", "Actuaciones Procesales - Resolucion judicial"),
        ("SUBASTA", "Incidentes Conexos - Medida cautelar"),
        ("RECURSO DE APELACION", "Actuaciones Procesales - Recurso"),
        ("HABILITACION DE DIAS", "Actuaciones Procesales - Escrito de parte"),
        ("ACOMPANA DOCUMENTAL", "Actuaciones Procesales - Escrito de parte"),
        ("TEXTO SIN PALABRAS CLAVE", "Sin clasificar"),
    ],
)
def test_categorizar(titulo, esperado):
    assert sep.categorizar(titulo) == esperado


def test_sin_acentos():
    assert sep.sin_acentos("acción ÁÉÍÓÚ ñ") == "accion AEIOU n"


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("Demanda de Alimentos", "Demanda_de_Alimentos"),
        ("acción", "accion"),
        ("", "tramite"),
        ("///", "tramite"),
    ],
)
def test_slug(texto, esperado):
    assert sep.slug(texto) == esperado


def test_slug_trunca():
    assert len(sep.slug("x" * 200)) == 90
    assert not sep.slug("x" * 200).endswith("_")


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("informe.pdf", "informe.pdf"),
        ("informe", "informe.pdf"),
        ("../../etc/passwd", "passwd.pdf"),
        ("a:b?.pdf", "a_b_.pdf"),
        ("CON", "_CON.pdf"),
        ("", "tramite.pdf"),
    ],
)
def test_nombre_archivo_seguro(entrada, esperado):
    assert sep.nombre_archivo_seguro(entrada) == esperado


@pytest.mark.parametrize(
    ("archivo", "esperado"),
    [
        ("01_Mi_Tramite.pdf", "Mi Tramite"),
        ("07-Demanda.pdf", "Demanda"),
        ("Demanda.pdf", "Demanda"),
    ],
)
def test_nombre_desde_archivo(archivo, esperado):
    assert sep.nombre_desde_archivo(archivo) == esperado


def test_tramite_calcula_rangos():
    tramite = sep.Tramite("Demanda", 2, 5)
    assert tramite.paginas == "2-5"
    assert tramite.cantidad_paginas == 4
    assert tramite.to_dict() == {
        "archivo": "",
        "categoria": "Sin clasificar",
        "paginas": "2-5",
        "cant": 4,
    }


def test_tramite_deriva_nombre_y_sanea_archivo():
    tramite = sep.Tramite("", 1, 1, archivo="../01_Demanda.pdf")
    assert tramite.nombre == "Demanda"
    assert tramite.archivo == "01_Demanda.pdf"
