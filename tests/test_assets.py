"""Verifica los assets públicos del README y la ausencia de datos reales."""

from __future__ import annotations

import re
from pathlib import Path

from PIL import Image

LIMITE_GIF = 5_000_000

# Emojis y símbolos decorativos que no queremos en la documentación ni en el demo.
EMOJI = re.compile(
    "["
    "\U0001f000-\U0001faff"
    "\U00002600-\U000027bf"
    "\U00002b00-\U00002bff"
    "\U0001f1e6-\U0001f1ff"
    "\ufe0f"
    "]"
)

REFERENCIAS_PROHIBIDAS = ("3497364", "ExpedienteDigital", "Charata", "Chaco")


def test_demo_gif(raiz: Path) -> None:
    ruta = raiz / "assets" / "demo.gif"
    assert ruta.exists(), "Falta assets/demo.gif"
    assert ruta.stat().st_size < LIMITE_GIF, "El GIF supera los 5 MB"

    with Image.open(ruta) as imagen:
        assert imagen.size == (1200, 675)
        assert imagen.n_frames >= 50
        assert imagen.info.get("loop") == 0

        duracion = 0
        for indice in range(imagen.n_frames):
            imagen.seek(indice)
            duracion += imagen.info.get("duration", 0)
        assert 10_000 <= duracion <= 15_000


def test_demo_png(raiz: Path) -> None:
    ruta = raiz / "assets" / "demo.png"
    assert ruta.exists(), "Falta assets/demo.png"
    with Image.open(ruta) as imagen:
        assert imagen.size == (1200, 675)


def test_social_preview(raiz: Path) -> None:
    ruta = raiz / "assets" / "social-preview.png"
    assert ruta.exists(), "Falta assets/social-preview.png"
    with Image.open(ruta) as imagen:
        assert imagen.size == (1280, 640)


def test_logo(raiz: Path) -> None:
    png = raiz / "assets" / "logo.png"
    svg = raiz / "assets" / "logo.svg"
    assert png.exists(), "Falta assets/logo.png"
    assert svg.exists(), "Falta assets/logo.svg"
    with Image.open(png) as imagen:
        assert imagen.size == (512, 512)
    assert svg.read_text(encoding="utf-8").lstrip().startswith("<svg")


def test_readmes_bilingues(raiz: Path) -> None:
    espanol = raiz / "README.md"
    ingles = raiz / "README.en.md"
    assert espanol.exists()
    assert ingles.exists()
    assert "assets/demo.gif" in espanol.read_text(encoding="utf-8")
    assert "assets/demo.gif" in ingles.read_text(encoding="utf-8")
    assert "README.en.md" in espanol.read_text(encoding="utf-8")
    assert "README.md" in ingles.read_text(encoding="utf-8")


def test_sin_emojis(raiz: Path) -> None:
    archivos = [
        raiz / "README.md",
        raiz / "README.en.md",
        raiz / "CHANGELOG.md",
        raiz / "CONTRIBUTING.md",
        raiz / "SECURITY.md",
        raiz / "CODE_OF_CONDUCT.md",
        raiz / "ROADMAP.md",
        raiz / "docs" / "README.md",
        raiz / "docs" / "MAPA.md",
        raiz / "docs" / "PRIVACIDAD.md",
        raiz / "docs" / "DEMO.md",
        raiz / "docs" / "PUBLICAR.md",
        raiz / "docs" / "FAQ.md",
        raiz / "tools" / "demo" / "terminal.html",
        raiz / "tools" / "demo" / "marca.html",
        raiz / "tools" / "demo" / "datos.js",
    ]
    for archivo in archivos:
        texto = archivo.read_text(encoding="utf-8")
        coincidencia = EMOJI.search(texto)
        assert coincidencia is None, f"Emoji en {archivo}: {coincidencia!r}"


def test_sin_referencias_reales(raiz: Path) -> None:
    archivos = [
        raiz / "README.md",
        raiz / "README.en.md",
        raiz / "assets" / "demo.gif",
        raiz / "assets" / "demo.png",
        raiz / "tools" / "demo" / "datos.js",
        raiz / "tools" / "demo" / "terminal.html",
    ]
    for archivo in archivos:
        if archivo.suffix in {".gif", ".png"}:
            continue
        texto = archivo.read_text(encoding="utf-8")
        for referencia in REFERENCIAS_PROHIBIDAS:
            assert referencia not in texto, f"{referencia} en {archivo}"


def test_version_documentada(raiz: Path) -> None:
    import separador_expediente

    changelog = (raiz / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"[{separador_expediente.__version__}]" in changelog
