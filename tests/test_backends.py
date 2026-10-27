"""Tests de los backends de PDF."""

from __future__ import annotations

import importlib.util

import pytest

import separador_expediente as sep


def _pymupdf_disponible() -> bool:
    return (
        importlib.util.find_spec("pymupdf") is not None
        or importlib.util.find_spec("fitz") is not None
    )


def test_backend_pypdf(pdf_bookmarks):
    marcadores = sep.leer_marcadores(pdf_bookmarks, backend="pypdf")

    assert len(marcadores) == 9
    assert marcadores[0].pagina == 1


def test_backend_desconocido(pdf_bookmarks):
    with pytest.raises(sep.ErrorSeparador, match="Backend desconocido"):
        sep.leer_marcadores(pdf_bookmarks, backend="otro")


@pytest.mark.skipif(
    not _pymupdf_disponible(), reason="PyMuPDF no está instalado"
)
def test_backend_pymupdf(pdf_bookmarks, tmp_path):
    marcadores = sep.leer_marcadores(pdf_bookmarks, backend="pymupdf")
    assert len(marcadores) == 9

    resultado = sep.dividir_expediente(
        pdf_bookmarks,
        tmp_path,
        agrupar="fecha",
        backend="pymupdf",
    )
    assert len(resultado) == 8
    assert (
        sep.verificar_salida(tmp_path, resultado, backend="pypdf") == []
    )
