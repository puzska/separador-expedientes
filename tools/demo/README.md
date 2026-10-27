# Demo

Genera el GIF, el PNG de fallback, el social preview y el logo del README.

```bat
npm install
python generar_datos.py
node grabar_demo.mjs
python ensamblar_gif.py
node generar_marca.mjs
```

- `generar_datos.py`: corre el CLI sobre el PDF sintético y escribe `datos.js`.
- `grabar_demo.mjs`: captura frames con Playwright.
- `ensamblar_gif.py`: arma `assets/demo.gif` y `assets/demo.png` con Pillow.
- `generar_marca.mjs`: genera `assets/social-preview.png` y `assets/logo.png`.

El detalle completo está en [docs/DEMO.md](../../docs/DEMO.md).

No agregues emojis ni datos reales. No commitees `node_modules/` ni `frames/`.
