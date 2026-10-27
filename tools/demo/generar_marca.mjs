/**
 * Genera assets/social-preview.png y assets/logo.png con Playwright.
 *
 * Uso:
 *   node generar_marca.mjs
 */
import { chromium } from "playwright";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const AQUI = path.dirname(fileURLToPath(import.meta.url));
const RAIZ = path.resolve(AQUI, "..", "..");
const ASSETS = path.join(RAIZ, "assets");
const HTML = pathToFileURL(path.join(AQUI, "marca.html")).href;

fs.mkdirSync(ASSETS, { recursive: true });

const browser = await chromium.launch();

async function capturar(tipo, ancho, alto, destino) {
  const page = await browser.newPage({
    viewport: { width: ancho, height: alto },
    deviceScaleFactor: 1,
  });
  await page.goto(`${HTML}?tipo=${tipo}`, { waitUntil: "load" });
  await page.evaluate(() => document.fonts.ready);
  await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(resolve)));

  const info = await page.evaluate(() => {
    const cardBody = document.querySelector(".card-body");
    const copy = document.querySelector(".copy");
    const foot = document.querySelector(".foot");
    const features = document.querySelector(".features");

    const rect = (el) => {
      const r = el.getBoundingClientRect();
      return { left: r.left, top: r.top, right: r.right, bottom: r.bottom };
    };

    const visibles = [...document.querySelectorAll(".eyebrow, h1, .sub, .features, .foot, .card")].filter(
      (el) => getComputedStyle(el).display !== "none" && el.getBoundingClientRect().width > 0
    );

    const rects = visibles.map((el) => ({
      tag: el.className || el.tagName,
      ...rect(el),
    }));

    const fuera = rects.filter(
      (r) =>
        r.left < -1 ||
        r.top < -1 ||
        r.right > window.innerWidth + 1 ||
        r.bottom > window.innerHeight + 1
    );

    const copyRect = copy && copy.getBoundingClientRect().width > 0 ? rect(copy) : null;
    const copyFuera = copyRect
      ? [...copy.children]
          .map((el) => ({ tag: el.className || el.tagName, ...rect(el) }))
          .filter(
            (r) =>
              r.left < copyRect.left - 1 ||
              r.top < copyRect.top - 1 ||
              r.right > copyRect.right + 1 ||
              r.bottom > copyRect.bottom + 1
          )
      : [];

    const footRect = foot && foot.getBoundingClientRect().width > 0 ? rect(foot) : null;
    const featuresRect =
      features && features.getBoundingClientRect().width > 0 ? rect(features) : null;
    const solapa =
      footRect && featuresRect ? featuresRect.bottom > footRect.top + 1 : false;

    return {
      scrollWidth: document.documentElement.scrollWidth,
      scrollHeight: document.documentElement.scrollHeight,
      bodyOverflow: cardBody ? cardBody.scrollHeight > cardBody.clientHeight + 1 : false,
      fuera,
      copyFuera,
      solapa,
    };
  });

  if (
    info.scrollWidth > ancho ||
    info.scrollHeight > alto ||
    info.bodyOverflow ||
    info.fuera.length > 0 ||
    info.copyFuera.length > 0 ||
    info.solapa
  ) {
    throw new Error(`Layout fuera de límites (${tipo}): ${JSON.stringify(info)}`);
  }

  await page.screenshot({ path: destino, animations: "disabled" });
  await page.close();
  console.log(`Generado: ${path.relative(RAIZ, destino)}`);
}

await capturar("social", 1280, 640, path.join(ASSETS, "social-preview.png"));
await capturar("logo", 512, 512, path.join(ASSETS, "logo.png"));

await browser.close();
