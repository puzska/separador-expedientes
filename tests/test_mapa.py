"""Tests de carga y guardado de mapas manuales (JSON y CSV)."""

from __future__ import annotations

import csv
import json

import pytest

import separador_expediente as sep


def test_cargar_mapa_json_de_ejemplo(mapa_json):
    tramites = sep.cargar_mapa(mapa_json)

    assert len(tramites) == 5
    assert tramites[0].archivo == "01_Demanda.pdf"
    assert tramites[0].nombre == "Demanda"
    assert tramites[0].paginas == "1-3"
    assert tramites[-1].paginas == "10-11"
    assert sum(t.cantidad_paginas for t in tramites) == 11


def test_cargar_mapa_csv_de_ejemplo(mapa_csv):
    tramites = sep.cargar_mapa(mapa_csv)

    assert len(tramites) == 5
    assert [t.paginas for t in tramites] == [
        "1-3",
        "4-4",
        "5-7",
        "8-9",
        "10-11",
    ]


def test_mapa_json_formatos_de_paginas(tmp_path):
    ruta = tmp_path / "mapa.json"
    ruta.write_text(
        json.dumps(
            [
                {"archivo": "01.pdf", "paginas": "1-2"},
                {"archivo": "02.pdf", "paginas": "3 a 4"},
                {"archivo": "03.pdf", "paginas": "5 hasta 6"},
                {"archivo": "04.pdf", "paginas": [7, 8]},
                {"archivo": "05.pdf", "pagina_inicio": 9, "pagina_fin": 10},
                {"archivo": "06.pdf", "cant": 2},
            ]
        ),
        encoding="utf-8",
    )

    tramites = sep.cargar_mapa(ruta)

    assert [t.paginas for t in tramites] == [
        "1-2",
        "3-4",
        "5-6",
        "7-8",
        "9-10",
        "11-12",
    ]
    assert tramites[5].nombre == "06"


def test_mapa_json_claves_alternativas(tmp_path):
    ruta = tmp_path / "mapa.json"
    ruta.write_text(
        json.dumps(
            [
                {
                    "file": "01.pdf",
                    "title": "Demanda",
                    "category": "Escrito",
                    "page_start": 1,
                    "page_end": 3,
                }
            ]
        ),
        encoding="utf-8",
    )

    tramite = sep.cargar_mapa(ruta)[0]

    assert tramite.archivo == "01.pdf"
    assert tramite.nombre == "Demanda"
    assert tramite.categoria == "Escrito"
    assert tramite.paginas == "1-3"


def test_mapa_json_envuelto_en_objeto(tmp_path):
    ruta = tmp_path / "mapa.json"
    ruta.write_text(
        json.dumps(
            {
                "tramites": [
                    {"archivo": "01.pdf", "paginas": "1-1"},
                ]
            }
        ),
        encoding="utf-8",
    )

    tramites = sep.cargar_mapa(ruta)
    assert len(tramites) == 1
    assert tramites[0].paginas == "1-1"


@pytest.mark.parametrize("delimitador", [",", ";", "\t", "|"])
def test_mapa_csv_delimitadores(tmp_path, delimitador):
    ruta = tmp_path / "mapa.csv"
    with open(ruta, "w", encoding="utf-8-sig", newline="") as archivo:
        writer = csv.writer(archivo, delimiter=delimitador)
        writer.writerow(["archivo", "nombre", "categoria", "paginas"])
        writer.writerow(["01.pdf", "Demanda", "Escrito", "1-2"])
        writer.writerow(["02.pdf", "Providencia", "Resolucion", "3-4"])

    tramites = sep.cargar_mapa(ruta)

    assert [t.nombre for t in tramites] == ["Demanda", "Providencia"]
    assert [t.paginas for t in tramites] == ["1-2", "3-4"]


def test_mapa_inexistente(tmp_path):
    with pytest.raises(FileNotFoundError):
        sep.cargar_mapa(tmp_path / "no_existe.json")


@pytest.mark.parametrize(
    "contenido",
    [
        json.dumps({"mapa": []}),
        json.dumps([]),
        json.dumps(["texto"]),
        json.dumps([{"archivo": "01.pdf"}]),
        json.dumps([{"archivo": "01.pdf", "cant": "dos"}]),
        "no es json",
    ],
)
def test_mapa_invalido(tmp_path, contenido):
    ruta = tmp_path / "mapa.json"
    ruta.write_text(contenido, encoding="utf-8")

    with pytest.raises((sep.MapaInvalidoError, json.JSONDecodeError)):
        sep.cargar_mapa(ruta)


def test_guardar_mapa_json_roundtrip(tmp_path):
    originales = [
        sep.Tramite(
            "Demanda",
            1,
            3,
            categoria="Escrito",
            archivo="01_Demanda.pdf",
            fecha="04/03/2025",
            hora="09:15:22",
        ),
        sep.Tramite("Sentencia", 4, 5, categoria="Resolucion"),
    ]

    ruta = sep.guardar_mapa(originales, tmp_path / "mapa.json")
    recuperados = sep.cargar_mapa(ruta)

    assert [t.archivo for t in recuperados] == [
        "01_Demanda.pdf",
        "02_Sentencia.pdf",
    ]
    assert [t.paginas for t in recuperados] == ["1-3", "4-5"]
    assert recuperados[0].categoria == "Escrito"
    assert recuperados[0].fecha == "04/03/2025"
    assert recuperados[0].hora == "09:15:22"


def test_guardar_mapa_csv_roundtrip(tmp_path):
    originales = [sep.Tramite("Demanda", 1, 2, categoria="Escrito")]

    ruta = sep.guardar_mapa(originales, tmp_path / "mapa.csv")
    recuperados = sep.cargar_mapa(ruta)

    assert ruta.read_bytes().startswith(b"\xef\xbb\xbf")
    assert len(recuperados) == 1
    assert recuperados[0].nombre == "Demanda"
    assert recuperados[0].paginas == "1-2"


def test_guardar_mapa_crea_directorios(tmp_path):
    ruta = sep.guardar_mapa(
        [sep.Tramite("Demanda", 1, 1)],
        tmp_path / "sub" / "carpeta" / "mapa.json",
    )
    assert ruta.exists()
