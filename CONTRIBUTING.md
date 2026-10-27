# Cómo contribuir

Gracias por tomar el proyecto y querer mejorarlo. Las contribuciones de código,
documentación, ejemplos y reportes de errores son bienvenidas.

Antes de participar, leé el [Código de conducta](CODE_OF_CONDUCT.md).

## Regla principal: no datos reales

Este repositorio no debe contener expedientes, nombres, números de causa,
domicilios ni ningún otro dato de clientes o personas reales.

- Para tests y ejemplos usá únicamente PDFs sintéticos.
- Los PDFs de `ejemplos/` se regeneran con `python scripts/generar_ejemplo.py`.
- No adjuntes expedientes reales en issues, pull requests ni discusiones.
- Si necesitás mostrar un error, recrealo con un PDF ficticio o con texto
  inventado.
- Revisá `git status` y `git diff --stat` antes de commitear.

El `.gitignore` bloquea los `*.pdf` que no estén en `ejemplos/` o en `tests/`,
pero no reemplaza la revisión manual.

## Entorno de desarrollo

Se recomienda Python 3.9 o superior y un entorno virtual.

```bat
git clone https://github.com/puzska/separador-expedientes.git
cd separador-expedientes
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[dev]"
python -m pytest
```

En Linux o macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m pytest
```

El extra `dev` instala `pypdf`, `pytest`, `Pillow` y `ruff`.

## Tests

- Todo cambio de comportamiento debe traer un test.
- La suite tiene que pasar en Linux y Windows.
- No agregues dependencias obligatorias para funcionalidad opcional.
- Si tocás la detección, los mapas o la división, corré la suite completa:

```bat
python -m pytest
```

- Para un archivo en particular:

```bat
python -m pytest tests/test_deteccion.py -q
```

- Para el chequeo de estilo:

```bat
python -m ruff check .
```

## Ejemplos y fixtures

Los PDFs de ejemplo se generan sin dependencias externas:

```bat
python scripts/generar_ejemplo.py
```

Si cambiás el generador, regenerá los archivos y verificá que sigan siendo
ficticios. Cada página debe conservar la leyenda
`EJEMPLO FICTICIO - SIN DATOS REALES`.

## Demo y assets

El GIF del README se genera con una terminal HTML y Playwright. Los datos salen
de una corrida real del CLI sobre el PDF sintético.

```bat
cd tools\demo
npm install
python generar_datos.py
node grabar_demo.mjs
python ensamblar_gif.py
node generar_marca.mjs
```

Requisitos: Node.js 18 o superior, Chromium de Playwright y Pillow.

- El GIF final debe pesar menos de 5 MB.
- No agregues emojis a la terminal, al README ni a los assets.
- Si cambiás la salida del CLI, regenerá `datos.js` y el GIF.
- El detalle del pipeline está en [docs/DEMO.md](docs/DEMO.md).

## Estilo

- Python 3.9 compatible.
- Tipos en las funciones públicas.
- Nombres de variables y mensajes en español, coherentes con el resto del
  proyecto.
- Líneas de hasta 100 caracteres.
- Sin emojis en código, documentación ni mensajes de consola.
- Preferí funciones pequeñas y tests claros antes que abstracciones grandes.

## Pull requests

Antes de abrir un PR:

- [ ] La rama sale de `main` y tiene un nombre descriptivo.
- [ ] `python -m pytest` pasa.
- [ ] `python -m ruff check .` pasa.
- [ ] Agregué o actualicé tests.
- [ ] Actualicé `README.md`, `README.en.md` o `docs/` si cambió el uso.
- [ ] Actualicé `CHANGELOG.md` en `[Unreleased]`.
- [ ] No incluí PDFs, imágenes ni textos con datos reales.
- [ ] El PR explica el problema y la solución, no solo el cambio.

Si el cambio es grande, abrí primero un issue para acordar el enfoque.

## Reportes de errores

Usá la plantilla de issue e incluí:

- sistema operativo y versión de Python;
- versión del paquete (`separador-expedientes --version`);
- backend (`pypdf` o `PyMuPDF`);
- comando ejecutado;
- salida completa del error;
- características del PDF: bookmarks, texto extraíble, escaneado, protegido.

No adjuntes el expediente real. Si el problema depende del PDF, describí su
estructura o armá un ejemplo sintético mínimo.
