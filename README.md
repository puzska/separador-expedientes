# Separador de expedientes en trámites

**Español** | [English](https://github.com/puzska/separador-expedientes/blob/main/README.en.md)

[![CI](https://github.com/puzska/separador-expedientes/actions/workflows/ci.yml/badge.svg)](https://github.com/puzska/separador-expedientes/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](https://github.com/puzska/separador-expedientes/blob/main/LICENSE)

Herramienta para tomar un PDF de expediente digital y separarlo en **un PDF por
trámite**, generando además un índice en CSV y JSON.

<p align="center">
  <img src="https://raw.githubusercontent.com/puzska/separador-expedientes/main/assets/demo.gif" alt="Demo: separador-expedientes lista los trámites y genera un PDF por trámite" width="900">
</p>

<p align="center">
  <sub>Demo generado con la salida real del CLI sobre un expediente ficticio. <a href="https://github.com/puzska/separador-expedientes/blob/main/docs/DEMO.md">Cómo se genera</a>.</sub>
</p>

Funciona con expedientes que tengan bookmarks o texto extraíble, y con
escaneos si se le pasa un mapa manual. No está atada a un juzgado, a un sistema
de gestión ni a un formato de expediente determinado.

Se puede usar como **CLI** o importar como **módulo** desde otro programa (un
asistente legal, un gestor de causas, una app de carga de expedientes, etc.).


## Características

- Detección automática por bookmarks, incluyendo índices planos y anidados.
- Agrupación por fecha y hora, por día o por bookmark.
- Detección por texto para PDFs sin bookmarks.
- Mapa manual en JSON o CSV para respetar una separación hecha a mano.
- Generación de un mapa borrador editable.
- Índice en CSV (UTF-8 con BOM, compatible con Excel) y JSON.
- Validación de solapamientos y de páginas sin asignar.
- Verificación de los PDFs generados.
- Backend `pypdf` (recomendado) o `PyMuPDF`.
- Sin dependencias obligatorias: se instala el backend que ya uses.

## Requisitos

- Python 3.9 o superior.
- Una de estas librerías de PDF:
  - `pypdf` (recomendada): `pip install pypdf`
  - `PyMuPDF`: `pip install pymupdf`

Si están las dos instaladas, usa `pypdf`. También se puede forzar con
`--backend pypdf` o `--backend pymupdf`.

## Instalación

Desde PyPI (recomendado):

```bat
python -m pip install "separador-expedientes[pypdf]"
separador-expedientes --version
```

Si preferís PyMuPDF:

```bat
python -m pip install "separador-expedientes[pymupdf]"
```

Para desarrollo, desde el repositorio:

```bat
git clone https://github.com/puzska/separador-expedientes.git
cd separador-expedientes
python -m pip install -e ".[dev]"
```

También se puede usar sin instalar, copiando `separador_expediente.py` al
proyecto:

```bat
python separador_expediente.py "expediente.pdf" --listar
```

## Uso rápido

Los comandos de abajo usan el PDF ficticio incluido en `ejemplos/`. Reemplazalo
por la ruta de tu expediente.

### 1) Ver qué trámites detecta

```bat
separador-expedientes "ejemplos/expediente_sintetico.pdf" --listar
```

No divide nada. Muestra los rangos de páginas, la categoría y el nombre que
asignaría a cada trámite:

```text
  #  Paginas      Cant.  Categoria                                     Nombre
-----------------------------------------------------------------------------
  1  1-3              3  Actuaciones Procesales - Escrito de parte     DEMANDA DE ALIMENTOS
  2  4-4              1  Actuaciones Procesales - Resolucion judicial  PROVIDENCIA: TENGASE POR PRESENTADO
  3  5-5              1  Actuaciones Procesales - Resolucion judicial  LIBRAR OFICIO
  ...
Total: 8 trámites, 11 páginas.
```

### 2) Separar automáticamente

```bat
separador-expedientes "ejemplos/expediente_sintetico.pdf" -o "TRAMITES SEPARADOS"
```

Genera un PDF por trámite y el índice `INDICE_TRAMITES.csv/json`.

El modo automático:

1. usa los bookmarks del PDF;
2. elige el nivel de bookmarks más representativo;
3. si no hay bookmarks, o son insuficientes, intenta detectar los inicios de
   documento por el texto;
4. si tampoco hay texto, pide un mapa manual.

### 3) Elegir cómo agrupar

```bat
:: Un trámite por envío (misma fecha y hora). Es el modo por defecto.
separador-expedientes "expediente.pdf" -o salida --agrupar fecha

:: Un trámite por día: fusiona todas las actuaciones de la misma fecha.
separador-expedientes "expediente.pdf" -o salida --agrupar dia

:: Un trámite por bookmark, aunque compartan fecha y hora.
separador-expedientes "expediente.pdf" -o salida --agrupar marcador
```

`--agrupar fecha` es la opción más segura cuando el sistema exporta un bookmark
por envío con adjuntos. `--agrupar dia` compacta más, pero puede unir
actuaciones distintas del mismo día. `--agrupar marcador` sirve para revisar el
índice completo del PDF.

Con el ejemplo incluido: 8 trámites con `fecha`, 7 con `dia` y 9 con
`marcador`.

### 4) Forzar detección por texto

```bat
separador-expedientes "expediente.pdf" -o salida --modo texto
```

Útil para PDFs sin bookmarks pero con texto. Reconoce, entre otras señales:

- páginas que reinician la numeración en “1”;
- encabezados judiciales;
- fechas;
- títulos como DEMANDA, CONTESTA, SENTENCIA, PROVIDENCIA, OFICIO, NOTA DE
  SECRETARIA, etc.

Es una heurística. Conviene revisar siempre el resultado con `--listar`.

### 5) Anteponer el número de expediente

```bat
separador-expedientes "expediente.pdf" -o salida --prefijo "0000123_"
```

Los archivos quedan como `0000123_01_Demanda.pdf`, etc. Es útil cuando se
procesan varios expedientes en una misma carpeta.

### 6) Generar un mapa borrador

```bat
separador-expedientes "expediente.pdf" --generar-mapa "mapa_borrador.json"
```

Después se edita el JSON o CSV y se usa con `--mapa`. También se puede generar
en CSV:

```bat
separador-expedientes "expediente.pdf" --generar-mapa "mapa_borrador.csv"
```

### 7) Separar con un mapa curado

```bat
separador-expedientes "ejemplos/expediente_sintetico.pdf" -o salida --mapa "ejemplos/mapa_sintetico.json"
```

El mapa tiene prioridad sobre la detección automática. Sirve cuando se quiere
respetar una agrupación procesal hecha a mano.

## Documentación

- [Guía del mapa manual](https://github.com/puzska/separador-expedientes/blob/main/docs/MAPA.md)
- [Preguntas frecuentes](https://github.com/puzska/separador-expedientes/blob/main/docs/FAQ.md)
- [Privacidad y datos](https://github.com/puzska/separador-expedientes/blob/main/docs/PRIVACIDAD.md)
- [Demo y assets](https://github.com/puzska/separador-expedientes/blob/main/docs/DEMO.md)
- [Publicación y release](https://github.com/puzska/separador-expedientes/blob/main/docs/PUBLICAR.md)
- [Hoja de ruta](https://github.com/puzska/separador-expedientes/blob/main/ROADMAP.md)

## Opciones principales

| Opción | Qué hace |
|---|---|
| `-o, --salida` | Carpeta de salida. |
| `--mapa` | Usa un mapa JSON/CSV con cortes de página. |
| `--modo` | `auto`, `bookmarks` o `texto`. |
| `--agrupar` | `fecha`, `dia` o `marcador`. |
| `--prefijo` | Prefijo para los nombres de archivo. |
| `--solo-con-fecha` | Ignora bookmarks sin fecha. |
| `--sin-paginas-iniciales` | No crea un trámite para páginas previas al primer bookmark. |
| `--nivel` | Fuerza un nivel de bookmarks. |
| `--generar-mapa` | Guarda un mapa borrador para editar. |
| `--verificar` | Comprueba que cada PDF tenga las páginas esperadas. |
| `--sobrescribir` | Reemplaza archivos existentes. |
| `--permitir-huecos` | Permite páginas sin asignar. |
| `--sin-indice` | No genera CSV/JSON. |
| `--backend` | Fuerza `pypdf` o `pymupdf`. |

## Formato del mapa manual

El mapa es una lista JSON o un CSV con encabezados. Lo mínimo por fila es:

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

Campos aceptados:

- `archivo`: nombre del PDF de salida. Si se omite, se genera
  `01_Nombre_Del_Tramite.pdf`.
- `nombre`: título para mostrar y para generar el nombre si no hay `archivo`.
- `categoria`: texto libre.
- `paginas`: rango inclusivo `"1-3"`, `"1 a 3"`, `"1 hasta 3"` o lista `[1, 3]`.
- `pagina_inicio` / `pagina_fin`: alternativa a `paginas`.
- `cant`: si no hay páginas, calcula el rango en orden desde la página 1.
- `fecha` / `hora`: opcionales, solo informativos.

Las páginas son **1-based e inclusivas**: `"1-3"` incluye las páginas 1, 2 y 3.

El CSV puede usar coma, punto y coma, tabulación o `|` como separador; se
detecta automáticamente. La plantilla `plantilla_mapa.csv` se puede editar
directamente.

## Integración en otro programa

```python
from separador_expediente import detectar_tramites, dividir_expediente

# Opción A: detección y división en una sola llamada
resultado = dividir_expediente(
    "expediente.pdf",
    "salida",
    agrupar="fecha",       # "fecha", "dia" o "marcador"
    modo="auto",           # "auto", "bookmarks" o "texto"
    prefijo="0000123_",
)

for tramite in resultado:
    print(tramite.archivo, tramite.paginas, tramite.categoria)
```

También se puede separar la detección de la división:

```python
from separador_expediente import detectar_tramites, dividir_expediente

tramites = detectar_tramites("expediente.pdf", agrupar="fecha")
resultado = dividir_expediente(
    "expediente.pdf",
    "salida",
    tramites,
    sobrescribir=True,
)
```

Con progreso para una interfaz gráfica:

```python
def progreso(actual, total, tramite):
    print(f"{actual}/{total}: {tramite.archivo}")

dividir_expediente(
    "expediente.pdf",
    "salida",
    tramites,
    progreso=progreso,
)
```

En `ejemplo_integracion.py` hay un ejemplo ejecutable que, sin argumentos, usa
el PDF ficticio del repositorio:

```bat
python ejemplo_integracion.py
python ejemplo_integracion.py "expediente.pdf" "salida" --dividir
```

### API principal

| Función | Qué hace |
|---|---|
| `leer_marcadores(pdf)` | Devuelve los bookmarks como lista de `Marcador`. |
| `detectar_tramites(pdf, ...)` | Agrupa bookmarks o texto en `Tramite` y calcula rangos. |
| `cargar_mapa(ruta)` | Carga un mapa JSON/CSV como lista de `Tramite`. |
| `guardar_mapa(tramites, ruta)` | Guarda un mapa editable en JSON o CSV. |
| `validar_tramites(tramites, total)` | Detecta solapamientos y páginas sin asignar. |
| `dividir_expediente(pdf, salida, ...)` | Genera los PDFs y el índice. |
| `verificar_salida(salida, tramites)` | Comprueba que cada PDF exista y tenga las páginas esperadas. |

Cada `Tramite` tiene:

```python
Tramite(
    nombre="...",
    pagina_inicio=1,
    pagina_fin=3,
    categoria="...",
    archivo="01_....pdf",   # opcional
    fecha="",               # opcional
    hora="",                # opcional
)
```

## Cómo funciona la detección automática

1. Lee el índice/bookmarks del PDF.
2. Elige el nivel de bookmarks más representativo. Esto cubre índices planos y
   también índices con un nodo raíz “Expediente” y los documentos en nivel 2.
3. Reconoce fechas en formatos como:
   - `04/12/2024 19:08:55`
   - `2025-02-03 11:42`
   - `04.12.2024`
   - `10/03/25`
   - fechas al inicio, al final o entre corchetes.
4. Normaliza fecha y hora para comparar y agrupar.
5. El final de cada trámite es la página anterior al inicio del siguiente, así
   que todas las páginas quedan asignadas.
6. Limpia el título (quita “Esc. N adjuntos”, el nombre del profesional,
   prefijos como “DOCUMENTO -”, etc.) y asigna una categoría aproximada por
   palabras clave.
7. Si no hay bookmarks o hay uno solo en un PDF largo, en modo `auto` prueba la
   detección por texto.

La detección por texto es una ayuda, no una verdad procesal. Para una
separación exacta según el criterio de un juzgado, lo mejor es generar un mapa
borrador, revisarlo y volver a ejecutar con `--mapa`.

## Estructura del repositorio

```text
.
├── separador_expediente.py     # script y módulo (CLI + API)
├── ejemplo_integracion.py      # ejemplo de uso como módulo
├── pyproject.toml              # instalación, entry point y pytest
├── requirements.txt            # dependencia mínima (pypdf)
├── plantilla_mapa.csv          # plantilla de mapa manual
├── README.md                   # documentación en español
├── README.en.md                # documentación en inglés
├── CHANGELOG.md
├── CONTRIBUTING.md
├── SECURITY.md
├── CODE_OF_CONDUCT.md
├── ROADMAP.md
├── assets/                     # demo, social preview y logo
│   ├── demo.gif
│   ├── demo.png
│   ├── social-preview.png
│   ├── logo.svg
│   └── logo.png
├── ejemplos/                   # PDFs y mapas 100 % ficticios
│   ├── expediente_sintetico.pdf
│   ├── expediente_sin_bookmarks.pdf
│   ├── expediente_anidado.pdf
│   ├── expediente_inicial.pdf
│   ├── mapa_sintetico.json
│   └── mapa_sintetico.csv
├── docs/                       # guías, FAQ, privacidad y publicación
├── scripts/
│   ├── pdf_sintetico.py        # generador de PDFs sin dependencias
│   └── generar_ejemplo.py      # regenera los archivos de ejemplos/
├── tools/demo/                 # terminal HTML, Playwright y GIF
├── tests/                      # suite de pytest
└── .github/
    ├── workflows/ci.yml        # CI en Linux y Windows
    ├── workflows/release.yml   # PyPI y artefactos del release
    ├── ISSUE_TEMPLATE/
    └── dependabot.yml
```

Los PDFs de ejemplo se pueden regenerar con:

```bat
python scripts/generar_ejemplo.py
```

## Tests

```bat
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check .
```

La suite cubre parseo de fechas y títulos, categorización, bookmarks planos y
anidados, agrupaciones, detección por texto, mapas JSON/CSV, división,
índices, validaciones, verificación de salida, CLI y backends. También se
verifican el tamaño y las dimensiones de los assets del demo.

La integración continua corre los tests en Linux y Windows con Python 3.9,
3.12 y 3.13, y construye el sdist y el wheel.

## Datos y privacidad

- **Este repositorio no contiene expedientes reales.** Todos los PDFs de
  `ejemplos/` son sintéticos: se generan con `scripts/generar_ejemplo.py`, usan
  nombres inventados y llevan la leyenda `EJEMPLO FICTICIO - SIN DATOS REALES`
  en cada página.
- El `.gitignore` bloquea todos los `*.pdf` salvo los de `ejemplos/`, además de
  las carpetas de salida y los mapas generados.
- La herramienta procesa archivos locales: no sube nada a ningún servidor.
- Si hacés un fork o agregás casos de prueba, revisá `git status` antes de
  commitear para no publicar documentos de clientes.

La política completa está en [docs/PRIVACIDAD.md](https://github.com/puzska/separador-expedientes/blob/main/docs/PRIVACIDAD.md).

## Límites

- Los PDFs escaneados sin texto necesitan OCR o un mapa manual.
- Los PDFs protegidos con contraseña no se pueden separar.
- La categoría es orientativa; se puede reemplazar desde el mapa.
- La detección por texto es una heurística. Para una separación exacta según el
  criterio de un juzgado, conviene generar un mapa borrador, revisarlo y usar
  `--mapa`.

Ver también las [preguntas frecuentes](https://github.com/puzska/separador-expedientes/blob/main/docs/FAQ.md).

## Contribuir

Las contribuciones son bienvenidas. Leé [CONTRIBUTING.md](https://github.com/puzska/separador-expedientes/blob/main/CONTRIBUTING.md) y el
[Código de conducta](https://github.com/puzska/separador-expedientes/blob/main/CODE_OF_CONDUCT.md).

- No incluyas expedientes ni datos reales.
- Los cambios de comportamiento necesitan tests.
- Para vulnerabilidades, seguí [SECURITY.md](https://github.com/puzska/separador-expedientes/blob/main/SECURITY.md).

## Licencia

MIT. Ver [LICENSE](https://github.com/puzska/separador-expedientes/blob/main/LICENSE).
