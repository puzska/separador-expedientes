"""Tests de detección de trámites por bookmarks y por texto."""

from __future__ import annotations

import pytest

import separador_expediente as sep


def test_leer_marcadores_del_ejemplo(pdf_bookmarks):
    marcadores = sep.leer_marcadores(pdf_bookmarks)

    assert len(marcadores) == 9
    assert [m.nivel for m in marcadores] == [1] * 9
    assert [m.pagina for m in marcadores] == [1, 3, 4, 5, 6, 8, 9, 10, 11]

    primero = marcadores[0]
    assert primero.fecha == "04/03/2025"
    assert primero.hora == "09:15:22"
    assert primero.titulo_limpio == "DEMANDA DE ALIMENTOS"


@pytest.mark.parametrize(
    ("agrupar", "cantidad"),
    [("fecha", 8), ("dia", 7), ("marcador", 9)],
)
def test_deteccion_agrupaciones(pdf_bookmarks, agrupar, cantidad):
    tramites = sep.detectar_tramites(pdf_bookmarks, agrupar=agrupar)

    assert len(tramites) == cantidad
    assert sum(t.cantidad_paginas for t in tramites) == 11
    assert tramites[0].pagina_inicio == 1
    assert tramites[-1].pagina_fin == 11

    for actual, siguiente in zip(tramites, tramites[1:]):
        assert siguiente.pagina_inicio == actual.pagina_fin + 1


def test_agrupar_fecha_fusiona_mismo_envio(pdf_bookmarks):
    tramites = sep.detectar_tramites(pdf_bookmarks, agrupar="fecha")

    assert [t.paginas for t in tramites] == [
        "1-3",
        "4-4",
        "5-5",
        "6-7",
        "8-8",
        "9-9",
        "10-10",
        "11-11",
    ]
    assert tramites[0].nombre == "DEMANDA DE ALIMENTOS"
    assert tramites[0].fecha == "04/03/2025"
    assert tramites[0].hora == "09:15:22"


def test_agrupar_dia_fusiona_toda_la_fecha(pdf_bookmarks):
    tramites = sep.detectar_tramites(pdf_bookmarks, agrupar="dia")

    assert tramites[0].paginas == "1-4"
    assert tramites[0].nombre == "DEMANDA DE ALIMENTOS"
    assert tramites[1].paginas == "5-5"


def test_agrupar_marcador_no_fusiona(pdf_bookmarks):
    tramites = sep.detectar_tramites(pdf_bookmarks, agrupar="marcador")

    assert tramites[1].paginas == "3-3"
    assert tramites[1].nombre == "DOCUMENTAL - PARTIDA DE NACIMIENTO"
    assert tramites[1].categoria == "Sin clasificar"


def test_deteccion_de_bookmarks_anidados(pdf_anidado):
    marcadores = sep.leer_marcadores(pdf_anidado)
    assert sorted({m.nivel for m in marcadores}) == [1, 2]
    assert len([m for m in marcadores if m.nivel == 1]) == 1
    assert len([m for m in marcadores if m.nivel == 2]) == 3

    tramites = sep.detectar_tramites(pdf_anidado)
    assert len(tramites) == 3
    assert [t.paginas for t in tramites] == ["1-2", "3-4", "5-6"]
    assert tramites[0].nombre == "DEMANDA DE ALIMENTOS"


def test_nivel_forzado(pdf_anidado):
    tramites = sep.detectar_tramites(pdf_anidado, nivel=2)
    assert len(tramites) == 3


def test_nivel_inexistente(pdf_anidado):
    with pytest.raises(sep.SinMarcadoresError, match="nivel 99"):
        sep.detectar_tramites(pdf_anidado, nivel=99)


def test_paginas_iniciales_incluidas(pdf_inicial):
    tramites = sep.detectar_tramites(pdf_inicial)

    assert len(tramites) == 3
    assert tramites[0].nombre == "Paginas iniciales"
    assert tramites[0].paginas == "1-1"
    assert tramites[1].paginas == "2-3"


def test_paginas_iniciales_excluidas(pdf_inicial):
    tramites = sep.detectar_tramites(
        pdf_inicial, incluir_paginas_iniciales=False
    )

    assert len(tramites) == 2
    assert tramites[0].paginas == "2-3"


def test_incluir_sin_fecha(pdf_factory):
    pdf = pdf_factory(
        "sin_fecha.pdf",
        [["Pagina 1"], ["Pagina 2"], ["Pagina 3"]],
        [
            (1, "04/03/2025 10:00 - DEMANDA", 1),
            (1, "SIN FECHA", 2),
            (1, "05/03/2025 10:00 - PROVIDENCIA", 3),
        ],
    )

    con_fecha = sep.detectar_tramites(pdf, agrupar="marcador")
    sin_fecha = sep.detectar_tramites(
        pdf, agrupar="marcador", incluir_sin_fecha=False
    )

    assert len(con_fecha) == 3
    assert len(sin_fecha) == 2
    assert [t.nombre for t in sin_fecha] == ["DEMANDA", "PROVIDENCIA"]


def test_modo_texto(pdf_texto):
    tramites = sep.detectar_tramites(pdf_texto, modo="texto")

    assert len(tramites) == 6
    assert [t.paginas for t in tramites] == [
        "1-1",
        "2-2",
        "3-3",
        "4-4",
        "5-5",
        "6-6",
    ]
    assert [t.nombre for t in tramites] == [
        "DEMANDA DE ALIMENTOS",
        "CONTESTA DEMANDA",
        "SENTENCIA",
        "NOTA DE SECRETARIA",
        "OFICIO",
        "ACOMPANA OFICIO DILIGENCIADO",
    ]


def test_modo_auto_usa_texto_si_no_hay_bookmarks(pdf_texto):
    tramites = sep.detectar_tramites(pdf_texto)
    assert len(tramites) == 6


def test_modo_bookmarks_falla_sin_bookmarks(pdf_texto):
    with pytest.raises(sep.SinMarcadoresError, match="bookmarks"):
        sep.detectar_tramites(pdf_texto, modo="bookmarks")


def test_pdf_sin_texto_ni_bookmarks(pdf_factory):
    pdf = pdf_factory("vacio.pdf", [[""], [""]])

    with pytest.raises(sep.SinMarcadoresError):
        sep.detectar_tramites(pdf)


@pytest.mark.parametrize("agrupar", ["otro", "FECHA", ""])
def test_agrupar_invalido(pdf_bookmarks, agrupar):
    with pytest.raises(ValueError, match="agrupar"):
        sep.detectar_tramites(pdf_bookmarks, agrupar=agrupar)


@pytest.mark.parametrize("modo", ["otro", "AUTO", ""])
def test_modo_invalido(pdf_bookmarks, modo):
    with pytest.raises(ValueError, match="modo"):
        sep.detectar_tramites(pdf_bookmarks, modo=modo)


def test_pdf_inexistente(tmp_path):
    with pytest.raises(FileNotFoundError):
        sep.detectar_tramites(tmp_path / "no_existe.pdf")
