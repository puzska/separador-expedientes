/**
 * Captura frames deterministas de la terminal HTML con Playwright.
 *
 * Uso:
 *   npm install
 *   node grabar_demo.mjs
 *
 * Genera frames PNG en tools/demo/frames/. El GIF se arma con
 * tools/demo/ensamblar_gif.py.
 */
import { chromium } from "playwright";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const AQUI = path.dirname(fileURLToPath(import.meta.url));
const HTML = pathToFileURL(path.join(AQUI, "terminal.html")).href;
const FRAMES = path.join(AQUI, "frames");
const FPS = 12;
const FRAME_MS = 1000 / FPS;
const VIEWPORT = { width: 1200, height: 675 };
const ESCALA = 2;

fs.rmSync(FRAMES, { recursive: true, force: true });
fs.mkdirSync(FRAMES, { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage({
  viewport: VIEWPORT,
  deviceScaleFactor: ESCALA,
});

await page.goto(HTML, { waitUntil: "load" });
await page.evaluate(() => document.fonts.ready);
await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(resolve)));

const duracion = await page.evaluate(() => window.DEMO_DURATION);
if (!Number.isFinite(duracion) || duracion <= 0) {
  throw new Error("window.DEMO_DURATION no está definido.");
}

const total = Math.floor(duracion / FRAME_MS) + 1;
console.log(`Capturando ${total} frames (${FPS} fps, ${duracion} ms)...`);

async function verificarLayout(ms) {
  await page.evaluate((t) => window.renderFrame(t), ms);
  const info = await page.evaluate(() => {
    const body = document.querySelector(".body");
    const bodyRect = body.getBoundingClientRect();
    const contentRight = bodyRect.right - 26;
    const lines = [...document.querySelectorAll(".line")];
    const anchas = lines
      .map((el, i) => {
        const range = document.createRange();
        range.selectNodeContents(el);
        const rect = range.getBoundingClientRect();
        return {
          i,
          texto: el.textContent.slice(0, 80),
          ancho: Math.round(rect.width),
          derecha: Math.round(rect.right),
        };
      })
      .filter((linea) => linea.derecha > contentRight + 1);

    return {
      anchas,
      altoContenido: body.scrollHeight,
      altoVisible: body.clientHeight,
      anchoDocumento: document.documentElement.scrollWidth,
      altoDocumento: document.documentElement.scrollHeight,
    };
  });

  const desborda =
    info.anchas.length > 0 ||
    info.altoContenido > info.altoVisible + 1 ||
    info.anchoDocumento > VIEWPORT.width ||
    info.altoDocumento > VIEWPORT.height;

  if (desborda) {
    throw new Error(`Layout fuera de límites en t=${ms}: ${JSON.stringify(info)}`);
  }
}

await verificarLayout(4050);
await verificarLayout(12500);
console.log("Layout verificado en t=4050 y t=12500.");

for (let i = 0; i < total; i += 1) {
  const t = Math.round(i * FRAME_MS);
  await page.evaluate((ms) => window.renderFrame(ms), t);
  const archivo = path.join(FRAMES, `frame_${String(i).padStart(4, "0")}.png`);
  await page.screenshot({ path: archivo, animations: "disabled" });
  if (i % 30 === 0 || i === total - 1) {
    console.log(`  ${i + 1}/${total} (t=${t} ms)`);
  }
}

const info = await page.evaluate(() => {
  const body = document.querySelector(".body");
  return {
    lineas: document.querySelectorAll(".line").length,
    altoContenido: body.scrollHeight,
    altoVisible: body.clientHeight,
  };
});
console.log("Layout final:", JSON.stringify(info));

await browser.close();
console.log(`Listo: ${FRAMES}`);
