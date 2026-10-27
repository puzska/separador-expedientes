"""Ensambla los frames de Playwright en ``assets/demo.gif``.

También genera ``assets/demo.png``, el fallback estático del README.

Uso::

    python tools/demo/ensamblar_gif.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parents[2]
FRAMES = Path(__file__).resolve().parent / "frames"
ASSETS = RAIZ / "assets"
GIF = ASSETS / "demo.gif"
PNG = ASSETS / "demo.png"

ANCHO = 1200
ALTO = 675
FPS = 12
DURACION_MS = round(1000 / FPS)
COLORES = 128
LIMITE_BYTES = 5_000_000


def _frames() -> list[Path]:
    archivos = sorted(FRAMES.glob("frame_*.png"))
    if not archivos:
        raise SystemExit(
            "No hay frames. Ejecutá primero: node tools/demo/grabar_demo.mjs"
        )
    return archivos


def _abrir(ruta: Path) -> Image.Image:
    imagen = Image.open(ruta).convert("RGB")
    if imagen.size != (ANCHO, ALTO):
        imagen = imagen.resize((ANCHO, ALTO), Image.Resampling.LANCZOS)
    return imagen


def _guardar_gif(imagenes: list[Image.Image], colores: int) -> int:
    paletas = [
        imagen.convert("P", palette=Image.Palette.ADAPTIVE, colors=colores)
        for imagen in imagenes
    ]
    paletas[0].save(
        GIF,
        save_all=True,
        append_images=paletas[1:],
        duration=DURACION_MS,
        loop=0,
        optimize=True,
        disposal=2,
    )
    return GIF.stat().st_size


def main() -> int:
    ASSETS.mkdir(parents=True, exist_ok=True)
    archivos = _frames()
    imagenes = [_abrir(ruta) for ruta in archivos]

    # Fallback estático: la tabla completa de --listar.
    indice_png = min(
        len(imagenes) - 1,
        round((4050 / 1000) * FPS),
    )
    imagenes[indice_png].save(PNG, format="PNG", optimize=True)

    tamano = _guardar_gif(imagenes, COLORES)
    if tamano > LIMITE_BYTES:
        tamano = _guardar_gif(imagenes, 64)

    kb = tamano / 1024
    print(f"GIF: {GIF.relative_to(RAIZ)}")
    print(f"  frames: {len(imagenes)}")
    print(f"  tamaño: {kb:.0f} KB")
    print(f"  límite: {LIMITE_BYTES / 1024:.0f} KB")
    if tamano > LIMITE_BYTES:
        print("  ADVERTENCIA: el GIF supera el límite de 5 MB.")
    print(f"PNG: {PNG.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
