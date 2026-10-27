"""Tests de la interfaz de línea de comandos."""

from __future__ import annotations

import json

import pytest

import separador_expediente as sep


def test_version(capsys):
    with pytest.raises(SystemExit) as excinfo:
        sep.main(["--version"])

    assert excinfo.value.code == 0
    assert sep.__version__ in capsys.readouterr().out


def test_listar(pdf_bookmarks, capsys):
    assert sep.main([str(pdf_bookmarks), "--listar"]) == 0

    salida = capsys.readouterr().out
    assert "Total: 8 trámites, 11 páginas." in salida
    assert "DEMANDA DE ALIMENTOS" in salida


def test_marcadores(pdf_bookmarks, capsys):
    assert sep.main([str(pdf_bookmarks), "--marcadores"]) == 0
    assert "Total: 9 marcadores." in capsys.readouterr().out


def test_dividir(tmp_path, pdf_bookmarks):
    salida = tmp_path / "salida"

    assert sep.main([str(pdf_bookmarks), "-o", str(salida)]) == 0

    assert len(list(salida.glob("*.pdf"))) == 8
    assert (salida / "INDICE_TRAMITES.csv").exists()


def test_generar_mapa(tmp_path, pdf_bookmarks):
    ruta = tmp_path / "mapa.json"

    assert sep.main([str(pdf_bookmarks), "--generar-mapa", str(ruta)]) == 0

    assert len(sep.cargar_mapa(ruta)) == 8


def test_mapa_y_listar(tmp_path, pdf_bookmarks, mapa_csv):
    assert (
        sep.main(
            [str(pdf_bookmarks), "--mapa", str(mapa_csv), "--listar"]
        )
        == 0
    )


def test_verificar(tmp_path, pdf_bookmarks, capsys):
    salida = tmp_path / "salida"

    codigo = sep.main(
        [
            str(pdf_bookmarks),
            "-o",
            str(salida),
            "--verificar",
            "--silencioso",
        ]
    )

    assert codigo == 0
    assert "Verificación OK" in capsys.readouterr().out


def test_sin_indice(tmp_path, pdf_bookmarks):
    salida = tmp_path / "salida"

    assert (
        sep.main([str(pdf_bookmarks), "-o", str(salida), "--sin-indice"]) == 0
    )
    assert not (salida / "INDICE_TRAMITES.csv").exists()


def test_prefijo(tmp_path, pdf_bookmarks):
    salida = tmp_path / "salida"

    assert (
        sep.main(
            [
                str(pdf_bookmarks),
                "-o",
                str(salida),
                "--prefijo",
                "0000123_",
                "--silencioso",
            ]
        )
        == 0
    )

    archivos = sorted(p.name for p in salida.glob("*.pdf"))
    assert archivos[0] == "0000123_01_DEMANDA_DE_ALIMENTOS.pdf"


def test_silencioso(tmp_path, pdf_bookmarks, capsys):
    salida = tmp_path / "salida"

    assert (
        sep.main(
            [str(pdf_bookmarks), "-o", str(salida), "--silencioso"]
        )
        == 0
    )

    salida_consola = capsys.readouterr().out
    assert "[  1/  8]" not in salida_consola
    assert "Listo: 8 trámites" in salida_consola


def test_agrupar_dia(tmp_path, pdf_bookmarks, capsys):
    salida = tmp_path / "salida"

    assert (
        sep.main(
            [
                str(pdf_bookmarks),
                "-o",
                str(salida),
                "--agrupar",
                "dia",
                "--silencioso",
            ]
        )
        == 0
    )

    assert "Total: 7 trámites" in capsys.readouterr().out


def test_sin_salida_muestra_tabla(pdf_bookmarks, capsys):
    assert sep.main([str(pdf_bookmarks)]) == 0

    salida = capsys.readouterr().out
    assert "Total: 8 trámites" in salida
    assert "Para dividir el PDF" in salida


def test_pdf_inexistente(tmp_path, capsys):
    assert sep.main([str(tmp_path / "no.pdf")]) == 2
    assert "no existe el PDF" in capsys.readouterr().err


def test_conflicto_auto_y_mapa(pdf_bookmarks, mapa_json):
    with pytest.raises(SystemExit) as excinfo:
        sep.main(
            [
                str(pdf_bookmarks),
                "--auto",
                "--mapa",
                str(mapa_json),
            ]
        )

    assert excinfo.value.code == 2


def test_mapa_invalido(tmp_path, pdf_bookmarks, capsys):
    ruta = tmp_path / "mapa.json"
    ruta.write_text(json.dumps([{"archivo": "01.pdf"}]), encoding="utf-8")

    assert (
        sep.main([str(pdf_bookmarks), "--mapa", str(ruta), "--listar"]) == 2
    )
    assert "ERROR" in capsys.readouterr().err
