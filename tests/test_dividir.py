"""Tests de división del PDF, índices y verificación."""

from __future__ import annotations

import json

import pytest
from pypdf import PdfReader

import separador_expediente as sep


def _paginas(ruta):
    return len(PdfReader(str(ruta)).pages)


def test_dividir_genera_un_pdf_por_tramite(tmp_path, pdf_bookmarks):
    tramites = sep.detectar_tramites(pdf_bookmarks, agrupar="fecha")
    resultado = sep.dividir_expediente(pdf_bookmarks, tmp_path, tramites)

    assert len(resultado) == 8
    assert len(list(tmp_path.glob("*.pdf"))) == 8
    for tramite in resultado:
        ruta = tmp_path / tramite.archivo
        assert ruta.exists()
        assert _paginas(ruta) == tramite.cantidad_paginas
    assert sep.verificar_salida(tmp_path, resultado) == []


def test_indices_json_y_csv(tmp_path, pdf_bookmarks):
    tramites = sep.detectar_tramites(pdf_bookmarks, agrupar="fecha")
    resultado = sep.dividir_expediente(pdf_bookmarks, tmp_path, tramites)

    datos = json.loads(
        (tmp_path / "INDICE_TRAMITES.json").read_text(encoding="utf-8")
    )
    assert len(datos) == 8
    assert datos[0]["archivo"] == resultado[0].archivo
    assert datos[0]["paginas"] == "1-3"
    assert datos[0]["cant"] == 3

    lineas = (tmp_path / "INDICE_TRAMITES.csv").read_text(
        encoding="utf-8-sig"
    ).splitlines()
    assert lineas[0] == "Archivo,Categoria,Paginas,Cantidad de paginas"
    assert len(lineas) == 9


def test_prefijo_en_los_nombres(tmp_path, pdf_bookmarks):
    tramites = sep.detectar_tramites(pdf_bookmarks, agrupar="fecha")
    resultado = sep.dividir_expediente(
        pdf_bookmarks, tmp_path, tramites, prefijo="0000123_"
    )

    assert resultado[0].archivo == "0000123_01_DEMANDA_DE_ALIMENTOS.pdf"
    assert all(t.archivo.startswith("0000123_") for t in resultado)
    assert sep.verificar_salida(tmp_path, resultado) == []


def test_no_sobrescribe_por_defecto(tmp_path, pdf_bookmarks):
    tramites = sep.detectar_tramites(pdf_bookmarks, agrupar="fecha")
    sep.dividir_expediente(pdf_bookmarks, tmp_path, tramites)

    with pytest.raises(FileExistsError, match="Ya existen archivos"):
        sep.dividir_expediente(pdf_bookmarks, tmp_path, tramites)


def test_sobrescribir(tmp_path, pdf_bookmarks):
    tramites = sep.detectar_tramites(pdf_bookmarks, agrupar="fecha")
    sep.dividir_expediente(pdf_bookmarks, tmp_path, tramites)
    resultado = sep.dividir_expediente(
        pdf_bookmarks, tmp_path, tramites, sobrescribir=True
    )

    assert len(resultado) == 8
    assert len(list(tmp_path.glob("*.pdf"))) == 8


def test_mapa_tiene_prioridad(tmp_path, pdf_bookmarks, mapa_json):
    resultado = sep.dividir_expediente(
        pdf_bookmarks, tmp_path, mapa=mapa_json
    )

    assert len(resultado) == 5
    assert {t.archivo for t in resultado} == {
        "01_Demanda.pdf",
        "02_Providencia.pdf",
        "03_Contestacion.pdf",
        "04_Sentencia.pdf",
        "05_Oficios.pdf",
    }
    assert sep.verificar_salida(tmp_path, resultado) == []


def test_mapa_y_tramites_son_excluyentes(tmp_path, pdf_bookmarks, mapa_json):
    with pytest.raises(ValueError, match="no ambos"):
        sep.dividir_expediente(
            pdf_bookmarks,
            tmp_path,
            [sep.Tramite("Demanda", 1, 1)],
            mapa=mapa_json,
        )


def test_huecos_fallan_por_defecto(tmp_path, pdf_bookmarks):
    tramites = [sep.Tramite("Parcial", 1, 10)]

    with pytest.raises(sep.MapaInvalidoError, match="sin asignar"):
        sep.dividir_expediente(pdf_bookmarks, tmp_path, tramites)


def test_permitir_huecos(tmp_path, pdf_bookmarks, capsys):
    tramites = [sep.Tramite("Parcial", 1, 10)]

    resultado = sep.dividir_expediente(
        pdf_bookmarks, tmp_path, tramites, permitir_huecos=True
    )

    assert len(resultado) == 1
    assert _paginas(tmp_path / resultado[0].archivo) == 10
    assert "sin asignar" in capsys.readouterr().err


def test_progreso(tmp_path, pdf_bookmarks):
    tramites = sep.detectar_tramites(pdf_bookmarks, agrupar="fecha")
    llamadas = []

    sep.dividir_expediente(
        pdf_bookmarks,
        tmp_path,
        tramites,
        progreso=lambda actual, total, tramite: llamadas.append(
            (actual, total, tramite.archivo)
        ),
    )

    assert len(llamadas) == 8
    assert llamadas[0][0] == 1
    assert llamadas[-1][0] == 8
    assert all(total == 8 for _, total, _ in llamadas)


def test_sin_indice(tmp_path, pdf_bookmarks):
    tramites = sep.detectar_tramites(pdf_bookmarks, agrupar="fecha")
    sep.dividir_expediente(
        pdf_bookmarks, tmp_path, tramites, escribir_indice=False
    )

    assert not (tmp_path / "INDICE_TRAMITES.json").exists()
    assert not (tmp_path / "INDICE_TRAMITES.csv").exists()


def test_pdf_inexistente(tmp_path):
    with pytest.raises(FileNotFoundError):
        sep.dividir_expediente(tmp_path / "no.pdf", tmp_path / "salida")


def test_verificar_detecta_archivo_faltante(tmp_path, pdf_bookmarks):
    tramites = sep.detectar_tramites(pdf_bookmarks, agrupar="fecha")
    resultado = sep.dividir_expediente(pdf_bookmarks, tmp_path, tramites)
    (tmp_path / resultado[0].archivo).unlink()

    problemas = sep.verificar_salida(tmp_path, resultado)

    assert len(problemas) == 1
    assert "Falta el archivo" in problemas[0]


def test_verificar_detecta_paginas_incorrectas(tmp_path, pdf_bookmarks):
    sep.dividir_expediente(
        pdf_bookmarks,
        tmp_path,
        [sep.Tramite("Uno", 1, 1)],
        permitir_huecos=True,
    )
    tramite = sep.Tramite("Uno", 1, 2, archivo="01_Uno.pdf")

    problemas = sep.verificar_salida(tmp_path, [tramite])

    assert len(problemas) == 1
    assert "se esperaban 2" in problemas[0]


def test_verificar_detecta_pdf_ilegible(tmp_path):
    (tmp_path / "roto.pdf").write_text("no soy un pdf", encoding="utf-8")
    tramite = sep.Tramite("Roto", 1, 1, archivo="roto.pdf")

    problemas = sep.verificar_salida(tmp_path, [tramite])

    assert len(problemas) == 1
    assert "no se pudo leer" in problemas[0]


def test_backend_explicito(tmp_path, pdf_bookmarks):
    resultado = sep.dividir_expediente(
        pdf_bookmarks,
        tmp_path,
        agrupar="marcador",
        backend="pypdf",
        prefijo="x_",
    )

    assert len(resultado) == 9
    assert sep.verificar_salida(tmp_path, resultado, backend="pypdf") == []
