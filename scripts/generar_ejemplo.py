"""Genera los PDFs y mapas de ejemplo del repositorio.

Todo el contenido es ficticio. No se usa ningún expediente real.

Uso::

    python scripts/generar_ejemplo.py

Escribe en ``ejemplos/``:

- ``expediente_sintetico.pdf``: 11 páginas con bookmarks y fechas variadas.
- ``expediente_sin_bookmarks.pdf``: 6 páginas con texto, sin bookmarks.
- ``expediente_anidado.pdf``: bookmarks con un nodo raíz y documentos en nivel 2.
- ``expediente_inicial.pdf``: la primera página no tiene bookmark.
- ``mapa_sintetico.json`` / ``mapa_sintetico.csv``: mapa manual de ejemplo.

Los archivos generados se pueden regenerar en cualquier momento. Si cambiás
los datos, volvé a correr este script y ejecutá los tests.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pdf_sintetico import crear_pdf  # noqa: E402

SALIDA = RAIZ / "ejemplos"

PAGINAS_CON_BOOKMARKS: list[list[str]] = [
    [
        "JUZGADO DE FAMILIA N 1",
        "CIUDAD FICTICIA",
        "",
        "Expediente N 0000123/2025",
        "PEREZ, JUAN C/ GOMEZ, ANA S/ ALIMENTOS",
        "",
        "DEMANDA DE ALIMENTOS",
        "",
        "Actor: PEREZ, JUAN",
        "Demandada: GOMEZ, ANA",
        "",
        "Documento de ejemplo. No corresponde a ninguna causa real.",
    ],
    [
        "DOCUMENTAL",
        "Partida de nacimiento",
        "",
        "Se acompania documental ficticia.",
    ],
    [
        "PROVIDENCIA",
        "",
        "Ciudad Ficticia, 04 de marzo de 2025",
        "",
        "TENGASE POR PRESENTADO",
        "",
        "Documento de ejemplo. No corresponde a ninguna causa real.",
    ],
    [
        "PROVIDENCIA",
        "",
        "Ciudad Ficticia, 05 de marzo de 2025",
        "",
        "LIBRAR OFICIO",
        "",
        "Documento de ejemplo. No corresponde a ninguna causa real.",
    ],
    [
        "CONTESTA DEMANDA",
        "",
        "La demandada contesta el traslado corrido.",
        "",
        "Documento de ejemplo. No corresponde a ninguna causa real.",
    ],
    [
        "CONTESTA DEMANDA",
        "",
        "Continuacion de la contestacion.",
        "",
        "Documento de ejemplo. No corresponde a ninguna causa real.",
    ],
    [
        "SENTENCIA",
        "",
        "Ciudad Ficticia, 20 de marzo de 2025",
        "",
        "RESUELVO: hacer lugar a la demanda.",
        "",
        "Documento de ejemplo. No corresponde a ninguna causa real.",
    ],
    [
        "NOTA DE SECRETARIA",
        "",
        "Se deja constancia de la notificacion.",
        "",
        "Documento de ejemplo. No corresponde a ninguna causa real.",
    ],
    [
        "OFICIO DILIGENCIADO",
        "",
        "Oficio ficticio diligenciado por el registro civil.",
        "",
        "Documento de ejemplo. No corresponde a ninguna causa real.",
    ],
    [
        "ACOMPANA OFICIO",
        "",
        "Se acompania el oficio diligenciado.",
        "",
        "Documento de ejemplo. No corresponde a ninguna causa real.",
    ],
    [
        "ESCRITO DE PARTE",
        "",
        "Se solicita tener presente lo informado.",
        "",
        "Documento de ejemplo. No corresponde a ninguna causa real.",
    ],
]

MARCADORES_CON_FECHAS: list[tuple[int, str, int]] = [
    (
        1,
        "04/03/2025 09:15:22 - DEMANDA DE ALIMENTOS - Esc. 2 adjuntos - Dr. Ficticio",
        1,
    ),
    (1, "04/03/2025 09:15:22 - DOCUMENTAL - PARTIDA DE NACIMIENTO", 3),
    (1, "04/03/2025 17:45:00 - PROVIDENCIA: TENGASE POR PRESENTADO", 4),
    (1, "05/03/2025 10:02 - LIBRAR OFICIO", 5),
    (1, "2025-03-12 08:30 - CONTESTA DEMANDA - Dra. Ejemplo", 6),
    (1, "20/03/2025 - SENTENCIA", 8),
    (1, "25/03/2025 11:45:10 - NOTA DE SECRETARIA", 9),
    (1, "02.04.2025 09:00 - OFICIO DILIGENCIADO", 10),
    (1, "10/04/25 16:20 - ACOMPANA OFICIO", 11),
]

PAGINAS_SIN_BOOKMARKS: list[list[str]] = [
    [
        "JUZGADO DE FAMILIA N 1",
        "Expediente N 0000123/2025",
        "DEMANDA DE ALIMENTOS",
        "PEREZ, JUAN C/ GOMEZ, ANA",
        "Documento de ejemplo. No corresponde a ninguna causa real.",
    ],
    [
        "12/03/2025",
        "CONTESTA DEMANDA",
        "La demandada contesta el traslado.",
        "Documento de ejemplo. No corresponde a ninguna causa real.",
    ],
    [
        "JUZGADO DE FAMILIA N 1",
        "Expediente N 0000123/2025",
        "SENTENCIA",
        "RESUELVO: hacer lugar a la demanda.",
        "Documento de ejemplo. No corresponde a ninguna causa real.",
    ],
    [
        "1",
        "NOTA DE SECRETARIA",
        "Se deja constancia de la notificacion.",
        "Documento de ejemplo. No corresponde a ninguna causa real.",
    ],
    [
        "OFICIO",
        "A la Direccion de Registro Civil",
        "Solicito informe.",
        "Documento de ejemplo. No corresponde a ninguna causa real.",
    ],
    [
        "20/04/2025",
        "ACOMPANA OFICIO DILIGENCIADO",
        "Se acompania el oficio.",
        "Documento de ejemplo. No corresponde a ninguna causa real.",
    ],
]

PAGINAS_ANIDADAS: list[list[str]] = [
    ["EXPEDIENTE 0000123/2025", "Caratula del expediente ficticio."],
    ["DEMANDA DE ALIMENTOS", "Escrito inicial."],
    ["PROVIDENCIA", "Tengase por presentado."],
    ["PROVIDENCIA", "Continuacion."],
    ["SENTENCIA", "Resuelvo."],
    ["SENTENCIA", "Continuacion."],
]

MARCADORES_ANIDADOS: list[tuple[int, str, int]] = [
    (1, "EXPEDIENTE 0000123/2025", 1),
    (2, "04/03/2025 09:15:22 - DEMANDA DE ALIMENTOS", 1),
    (2, "05/03/2025 10:02 - PROVIDENCIA", 3),
    (2, "10/03/2025 09:00 - SENTENCIA", 5),
]

PAGINAS_INICIAL: list[list[str]] = [
    ["CARATULA", "Pagina sin bookmark."],
    ["DEMANDA DE ALIMENTOS", "Escrito inicial."],
    ["DEMANDA DE ALIMENTOS", "Continuacion."],
    ["PROVIDENCIA", "Tengase por presentado."],
]

MARCADORES_INICIAL: list[tuple[int, str, int]] = [
    (1, "05/03/2025 10:00 - DEMANDA DE ALIMENTOS", 2),
    (1, "06/03/2025 11:00 - PROVIDENCIA", 4),
]

MAPA_EJEMPLO: list[dict[str, str]] = [
    {
        "archivo": "01_Demanda.pdf",
        "nombre": "Demanda",
        "categoria": "Actuaciones Procesales - Escrito de parte",
        "paginas": "1-3",
    },
    {
        "archivo": "02_Providencia.pdf",
        "nombre": "Providencia",
        "categoria": "Actuaciones Procesales - Resolucion judicial",
        "paginas": "4-4",
    },
    {
        "archivo": "03_Contestacion.pdf",
        "nombre": "Contestacion",
        "categoria": "Actuaciones Procesales - Contestacion",
        "paginas": "5-7",
    },
    {
        "archivo": "04_Sentencia.pdf",
        "nombre": "Sentencia",
        "categoria": "Actuaciones Procesales - Resolucion judicial",
        "paginas": "8-9",
    },
    {
        "archivo": "05_Oficios.pdf",
        "nombre": "Oficios",
        "categoria": "Actuaciones Procesales - Oficio",
        "paginas": "10-11",
    },
]


def generar(salida: Path = SALIDA) -> list[Path]:
    """Genera todos los archivos de ejemplo y devuelve sus rutas."""
    salida.mkdir(parents=True, exist_ok=True)
    generados: list[Path] = []

    generados.append(
        crear_pdf(
            salida / "expediente_sintetico.pdf",
            paginas=PAGINAS_CON_BOOKMARKS,
            marcadores=MARCADORES_CON_FECHAS,
        )
    )
    generados.append(
        crear_pdf(
            salida / "expediente_sin_bookmarks.pdf",
            paginas=PAGINAS_SIN_BOOKMARKS,
        )
    )
    generados.append(
        crear_pdf(
            salida / "expediente_anidado.pdf",
            paginas=PAGINAS_ANIDADAS,
            marcadores=MARCADORES_ANIDADOS,
        )
    )
    generados.append(
        crear_pdf(
            salida / "expediente_inicial.pdf",
            paginas=PAGINAS_INICIAL,
            marcadores=MARCADORES_INICIAL,
        )
    )

    ruta_json = salida / "mapa_sintetico.json"
    with open(ruta_json, "w", encoding="utf-8", newline="\n") as archivo:
        archivo.write(json.dumps(MAPA_EJEMPLO, ensure_ascii=False, indent=2) + "\n")
    generados.append(ruta_json)

    ruta_csv = salida / "mapa_sintetico.csv"
    with open(ruta_csv, "w", encoding="utf-8-sig", newline="") as archivo:
        writer = csv.DictWriter(
            archivo,
            fieldnames=["archivo", "nombre", "categoria", "paginas"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(MAPA_EJEMPLO)
    generados.append(ruta_csv)

    return generados


def main() -> int:
    for ruta in generar():
        print(f"Generado: {ruta.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
