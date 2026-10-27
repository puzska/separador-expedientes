# Demo y assets

El README usa `assets/demo.gif`. No es una captura de una terminal real: es una
terminal HTML renderizada por Playwright, alimentada con la salida real del CLI.

## Qué muestra el GIF

1. `separador-expedientes expediente.pdf --listar`
2. La tabla de trámites detectados.
3. `separador-expedientes expediente.pdf -o "TRAMITES SEPARADOS"`
4. El progreso y el índice.
5. `Get-ChildItem "TRAMITES SEPARADOS" -Name`
6. Los PDFs y los índices generados.

El PDF usado es `ejemplos/expediente_sintetico.pdf`, copiado como
`expediente.pdf` en una carpeta temporal. La salida es la del CLI real; solo se
reemplazan las rutas temporales por `C:\casos\expediente-demo` y se omite la
tabla final que el CLI imprime después del índice para que el GIF no sea
demasiado largo.

## Pipeline

```bat
cd tools\demo
npm install
python generar_datos.py
node grabar_demo.mjs
python ensamblar_gif.py
node generar_marca.mjs
```

### `generar_datos.py`

- Copia el PDF sintético a una carpeta temporal.
- Ejecuta `--listar` y una división.
- Sanitiza las rutas.
- Escribe `tools/demo/datos.js` con la salida real.

### `grabar_demo.mjs`

- Abre `terminal.html` con Playwright.
- Renderiza 151 frames a 12 fps con `window.renderFrame(t)`.
- Captura a 2x y deja los PNG en `tools/demo/frames/`.
- Verifica que no haya desbordes horizontales ni verticales en los momentos
  clave antes de capturar.

La animación es determinista: no depende de tiempos reales del sistema. El HTML
calcula el estado a partir del tiempo `t`.

### `ensamblar_gif.py`

- Redimensiona los frames a 1200x675.
- Genera `assets/demo.gif` con Pillow.
- Fusiona frames idénticos y ajusta la duración resultante.
- Genera `assets/demo.png`, el fallback estático.
- Si el GIF supera 5 MB, reintenta con menos colores.

### `generar_marca.mjs`

- Genera `assets/social-preview.png` (1280x640).
- Genera `assets/logo.png` (512x512) a partir del SVG de marca.

## Requisitos

- Node.js 18 o superior.
- Playwright con Chromium:
  ```bat
  npx playwright install chromium
  ```
- Pillow (incluido en el extra `dev`):
  ```bat
  python -m pip install -e ".[dev]"
  ```

## Reglas de diseño

- Sin emojis.
- Tema oscuro, tipografía monoespaciada.
- Nada de datos reales.
- El GIF final debe pesar menos de 5 MB.
- El texto de la tabla tiene que entrar sin cortes horizontales.
- El layout se verifica con las mismas medidas del DOM antes de capturar.

## Regenerar después de un cambio

Si cambia la salida del CLI:

```bat
cd tools\demo
python generar_datos.py
node grabar_demo.mjs
python ensamblar_gif.py
```

Si cambia el diseño de la terminal, editá `terminal.html` y repetí el pipeline.
Si cambia la marca, editá `marca.html` y `assets/logo.svg`, y ejecutá
`node generar_marca.mjs`.

## Archivos que no se versionan

- `tools/demo/frames/` (frames intermedios).
- `tools/demo/node_modules/`.

El GIF, el PNG, el social preview y el logo sí se versionan para que el README
funcione sin regenerar nada.
