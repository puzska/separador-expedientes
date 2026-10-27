# Court Case PDF Splitter

[Español](https://github.com/puzska/separador-expedientes/blob/main/README.md) | **English**

[![CI](https://github.com/puzska/separador-expedientes/actions/workflows/ci.yml/badge.svg)](https://github.com/puzska/separador-expedientes/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/separador-expedientes)](https://pypi.org/project/separador-expedientes/)
[![Release](https://img.shields.io/github/v/release/puzska/separador-expedientes)](https://github.com/puzska/separador-expedientes/releases)
[![Python](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](https://github.com/puzska/separador-expedientes/blob/main/LICENSE)

Take a court case file exported as a single PDF and split it into **one PDF per
proceeding**, with a CSV and JSON index.

<p align="center">
  <img src="https://raw.githubusercontent.com/puzska/separador-expedientes/main/assets/demo.gif" alt="Demo: separador-expedientes lists the proceedings and creates one PDF per proceeding" width="900">
</p>

<p align="center">
  <sub>Demo generated from the real CLI output on a fictional case file. <a href="https://github.com/puzska/separador-expedientes/blob/main/docs/DEMO.md">How it is generated</a>.</sub>
</p>

It works with PDFs that have bookmarks or extractable text, and with scanned
PDFs when you provide a manual page map. It is not tied to a specific court,
case-management system, or export format.

You can use it as a **CLI** or import it as a **module** from another program
(a legal assistant, a case-management tool, a document intake app, etc.).

The CLI messages and the sample output are in Spanish. The module API and the
documentation in `docs/` are also in Spanish, except for this README.

## Features

- Automatic detection from bookmarks, including flat and nested indexes.
- Grouping by date and time, by day, or by bookmark.
- Text-based detection for PDFs without bookmarks.
- Manual map in JSON or CSV to preserve a hand-made split.
- Editable draft map generation.
- CSV index (UTF-8 with BOM, Excel-friendly) and JSON index.
- Overlap and unassigned-page validation.
- Verification of the generated PDFs.
- `pypdf` (recommended) or `PyMuPDF` backend.
- No mandatory dependencies: install the backend you already use.

## Requirements

- Python 3.9 or newer.
- One of these PDF libraries:
  - `pypdf` (recommended): `pip install pypdf`
  - `PyMuPDF`: `pip install pymupdf`

If both are installed, `pypdf` is used. You can force a backend with
`--backend pypdf` or `--backend pymupdf`.

## Installation

From PyPI (recommended):

```bat
python -m pip install "separador-expedientes[pypdf]"
separador-expedientes --version
```

With PyMuPDF instead:

```bat
python -m pip install "separador-expedientes[pymupdf]"
```

For development, from the repository:

```bat
git clone https://github.com/puzska/separador-expedientes.git
cd separador-expedientes
python -m pip install -e ".[dev]"
```

You can also run it without installing, by copying `separador_expediente.py`
into your project:

```bat
python separador_expediente.py "case-file.pdf" --listar
```

## Quick start

The examples below use the fictional PDF in `ejemplos/`. Replace it with the
path to your case file.

### 1) List the detected proceedings

```bat
separador-expedientes "ejemplos/expediente_sintetico.pdf" --listar
```

This does not split anything. It shows the page ranges, category, and output
name for each proceeding:

```text
  #  Paginas      Cant.  Categoria                                     Nombre
-----------------------------------------------------------------------------
  1  1-3              3  Actuaciones Procesales - Escrito de parte     DEMANDA DE ALIMENTOS
  2  4-4              1  Actuaciones Procesales - Resolucion judicial  PROVIDENCIA: TENGASE POR PRESENTADO
  3  5-5              1  Actuaciones Procesales - Resolucion judicial  LIBRAR OFICIO
  ...
Total: 8 trámites, 11 páginas.
```

### 2) Split automatically

```bat
separador-expedientes "ejemplos/expediente_sintetico.pdf" -o "TRAMITES SEPARADOS"
```

This creates one PDF per proceeding and the `INDICE_TRAMITES.csv/json` index.

The automatic mode:

1. uses the PDF bookmarks;
2. picks the most representative bookmark level;
3. if there are no bookmarks, or too few, tries to detect document starts from
   the text;
4. if there is no text either, asks for a manual map.

### 3) Choose how to group

```bat
:: One proceeding per filing (same date and time). This is the default.
separador-expedientes "case-file.pdf" -o output --agrupar fecha

:: One proceeding per day: merges all filings from the same date.
separador-expedientes "case-file.pdf" -o output --agrupar dia

:: One proceeding per bookmark, even if they share date and time.
separador-expedientes "case-file.pdf" -o output --agrupar marcador
```

`--agrupar fecha` is the safest choice when the system exports one bookmark per
filing with attachments. `--agrupar dia` is more compact but may merge distinct
filings from the same day. `--agrupar marcador` is useful to inspect the full
PDF index.

With the included example: 8 proceedings with `fecha`, 7 with `dia`, and 9 with
`marcador`.

### 4) Force text detection

```bat
separador-expedientes "case-file.pdf" -o output --modo texto
```

Useful for PDFs without bookmarks but with extractable text. It recognizes,
among other signals:

- pages that restart numbering at "1";
- court headers;
- dates;
- titles such as DEMANDA, CONTESTA, SENTENCIA, PROVIDENCIA, OFICIO, NOTA DE
  SECRETARIA, etc.

This is a heuristic. Always review the result with `--listar`.

### 5) Add a case number prefix

```bat
separador-expedientes "case-file.pdf" -o output --prefijo "0000123_"
```

Files become `0000123_01_Demanda.pdf`, etc. Useful when processing several case
files in the same folder.

### 6) Generate a draft map

```bat
separador-expedientes "case-file.pdf" --generar-mapa "draft_map.json"
```

Edit the JSON or CSV and use it with `--mapa`. You can also generate a CSV:

```bat
separador-expedientes "case-file.pdf" --generar-mapa "draft_map.csv"
```

### 7) Split with a curated map

```bat
separador-expedientes "ejemplos/expediente_sintetico.pdf" -o output --mapa "ejemplos/mapa_sintetico.json"
```

The map takes precedence over automatic detection. It is useful when you need
to preserve a procedural grouping made by hand.

## Main options

| Option | What it does |
|---|---|
| `-o, --salida` | Output folder. |
| `--mapa` | Uses a JSON/CSV map with page cuts. |
| `--modo` | `auto`, `bookmarks`, or `texto`. |
| `--agrupar` | `fecha`, `dia`, or `marcador`. |
| `--prefijo` | Prefix for output file names. |
| `--solo-con-fecha` | Ignores bookmarks without a date. |
| `--sin-paginas-iniciales` | Does not create a proceeding for pages before the first bookmark. |
| `--nivel` | Forces a bookmark level. |
| `--generar-mapa` | Saves an editable draft map. |
| `--verificar` | Checks that each PDF has the expected pages. |
| `--sobrescribir` | Replaces existing files. |
| `--permitir-huecos` | Allows unassigned pages. |
| `--sin-indice` | Does not generate the CSV/JSON index. |
| `--backend` | Forces `pypdf` or `pymupdf`. |

## Manual map format

The map is a JSON list or a CSV with headers. The minimum per row is:

```json
[
  {
    "archivo": "01_Demanda.pdf",
    "nombre": "Demanda",
    "categoria": "Actuaciones Procesales - Escrito de parte",
    "paginas": "1-3"
  }
]
```

Accepted fields:

- `archivo`: output PDF name. If omitted, it is generated from
  `01_Nombre_Del_Tramite.pdf`.
- `nombre`: display title and source for the file name if `archivo` is missing.
- `categoria`: free text.
- `paginas`: inclusive range `"1-3"`, `"1 a 3"`, `"1 hasta 3"`, or list `[1, 3]`.
- `pagina_inicio` / `pagina_fin`: alternative to `paginas`.
- `cant`: if there are no pages, calculates the range in order from page 1.
- `fecha` / `hora`: optional, informational only.

Pages are **1-based and inclusive**: `"1-3"` includes pages 1, 2, and 3.

The CSV can use comma, semicolon, tab, or `|` as a separator; it is detected
automatically. The `plantilla_mapa.csv` template can be edited directly.

The full guide is in [docs/MAPA.md](https://github.com/puzska/separador-expedientes/blob/main/docs/MAPA.md) (Spanish).

## Module API

```python
from separador_expediente import detectar_tramites, dividir_expediente

# Option A: detection and split in one call
resultado = dividir_expediente(
    "case-file.pdf",
    "output",
    agrupar="fecha",       # "fecha", "dia", or "marcador"
    modo="auto",           # "auto", "bookmarks", or "texto"
    prefijo="0000123_",
)

for tramite in resultado:
    print(tramite.archivo, tramite.paginas, tramite.categoria)
```

You can also separate detection from splitting:

```python
from separador_expediente import detectar_tramites, dividir_expediente

tramites = detectar_tramites("case-file.pdf", agrupar="fecha")
resultado = dividir_expediente(
    "case-file.pdf",
    "output",
    tramites,
    sobrescribir=True,
)
```

With progress for a GUI:

```python
def progreso(actual, total, tramite):
    print(f"{actual}/{total}: {tramite.archivo}")

dividir_expediente(
    "case-file.pdf",
    "output",
    tramites,
    progreso=progreso,
)
```

`ejemplo_integracion.py` is a runnable example that uses the fictional PDF when
called without arguments:

```bat
python ejemplo_integracion.py
python ejemplo_integracion.py "case-file.pdf" "output" --dividir
```

### Main API

| Function | What it does |
|---|---|
| `leer_marcadores(pdf)` | Returns the bookmarks as a list of `Marcador`. |
| `detectar_tramites(pdf, ...)` | Groups bookmarks or text into `Tramite` and calculates ranges. |
| `cargar_mapa(ruta)` | Loads a JSON/CSV map as a list of `Tramite`. |
| `guardar_mapa(tramites, ruta)` | Saves an editable map in JSON or CSV. |
| `validar_tramites(tramites, total)` | Detects overlaps and unassigned pages. |
| `dividir_expediente(pdf, salida, ...)` | Generates the PDFs and the index. |
| `verificar_salida(salida, tramites)` | Checks that each PDF exists and has the expected pages. |

Each `Tramite` has:

```python
Tramite(
    nombre="...",
    pagina_inicio=1,
    pagina_fin=3,
    categoria="...",
    archivo="01_....pdf",   # optional
    fecha="",               # optional
    hora="",                # optional
)
```

## How automatic detection works

1. Reads the PDF bookmark index.
2. Picks the most representative bookmark level. This covers flat indexes and
   indexes with an "Expediente" root node and the documents at level 2.
3. Recognizes dates in formats such as:
   - `04/12/2024 19:08:55`
   - `2025-02-03 11:42`
   - `04.12.2024`
   - `10/03/25`
   - dates at the beginning, at the end, or in brackets.
4. Normalizes date and time for comparison and grouping.
5. The end of each proceeding is the page before the next start, so every page
   is assigned.
6. Cleans the title (removes "Esc. N adjuntos", the professional's name,
   prefixes such as "DOCUMENTO -", etc.) and assigns an approximate category by
   keywords.
7. If there are no bookmarks, or only one in a long PDF, in `auto` mode it tries
   text detection.

Text detection is an aid, not a procedural truth. For an exact split based on a
court's criteria, generate a draft map, review it, and run again with `--mapa`.

## Repository structure

```text
.
├── separador_expediente.py     # script and module (CLI + API)
├── ejemplo_integracion.py      # module usage example
├── pyproject.toml              # packaging, entry point, and pytest
├── requirements.txt            # minimum dependency (pypdf)
├── plantilla_mapa.csv          # manual map template
├── README.md                   # Spanish documentation
├── README.en.md                # English documentation
├── CHANGELOG.md
├── CONTRIBUTING.md
├── SECURITY.md
├── CODE_OF_CONDUCT.md
├── ROADMAP.md
├── assets/                     # demo, social preview, and logo
│   ├── demo.gif
│   ├── demo.png
│   ├── social-preview.png
│   ├── logo.svg
│   └── logo.png
├── ejemplos/                   # 100% fictional PDFs and maps
│   ├── expediente_sintetico.pdf
│   ├── expediente_sin_bookmarks.pdf
│   ├── expediente_anidado.pdf
│   ├── expediente_inicial.pdf
│   ├── mapa_sintetico.json
│   └── mapa_sintetico.csv
├── docs/                       # guides, FAQ, privacy, and release notes
├── scripts/
│   ├── pdf_sintetico.py        # dependency-free PDF generator
│   └── generar_ejemplo.py      # regenerates the files in ejemplos/
├── tools/demo/                 # HTML terminal, Playwright, and GIF pipeline
├── tests/                      # pytest suite
└── .github/
    ├── workflows/ci.yml        # CI on Linux and Windows
    ├── workflows/release.yml   # PyPI and release assets
    ├── ISSUE_TEMPLATE/
    └── dependabot.yml
```

Regenerate the example PDFs with:

```bat
python scripts/generar_ejemplo.py
```

## Tests

```bat
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check .
```

The suite covers date and title parsing, categorization, flat and nested
bookmarks, grouping, text detection, JSON/CSV maps, splitting, indexes,
validation, output verification, CLI, and backends. It also checks the size and
dimensions of the demo assets.

CI runs the tests on Linux and Windows with Python 3.9, 3.12, and 3.13, and
builds the sdist and wheel.

## Data and privacy

- **This repository contains no real case files.** Every PDF in `ejemplos/` is
  synthetic: it is generated by `scripts/generar_ejemplo.py`, uses invented
  names, and includes the legend `EJEMPLO FICTICIO - SIN DATOS REALES` on every
  page.
- `.gitignore` blocks every `*.pdf` except those in `ejemplos/`, plus output
  folders and generated maps.
- The tool processes local files: it does not upload anything to a server.
- If you fork the project or add test cases, check `git status` before
  committing so you do not publish client documents.

The full policy is in [docs/PRIVACIDAD.md](https://github.com/puzska/separador-expedientes/blob/main/docs/PRIVACIDAD.md) (Spanish).

## Limits

- Scanned PDFs without text need OCR or a manual map.
- Password-protected PDFs cannot be split.
- The category is advisory; it can be replaced from the map.
- Text detection is a heuristic. For an exact split based on a court's
  criteria, generate a draft map, review it, and use `--mapa`.

See also the [FAQ](https://github.com/puzska/separador-expedientes/blob/main/docs/FAQ.md) (Spanish).

## Contributing

Contributions are welcome. Read [CONTRIBUTING.md](https://github.com/puzska/separador-expedientes/blob/main/CONTRIBUTING.md) and the
[Code of Conduct](https://github.com/puzska/separador-expedientes/blob/main/CODE_OF_CONDUCT.md).

- Do not include real case files or personal data.
- Behavior changes need tests.
- For vulnerabilities, follow [SECURITY.md](https://github.com/puzska/separador-expedientes/blob/main/SECURITY.md).

## License

MIT. See [LICENSE](https://github.com/puzska/separador-expedientes/blob/main/LICENSE).
