"""Configuración común de los tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
for ruta in (RAIZ, RAIZ / "scripts"):
    if str(ruta) not in sys.path:
        sys.path.insert(0, str(ruta))

from pdf_sintetico import crear_pdf  # noqa: E402


@pytest.fixture(scope="session")
def raiz() -> Path:
    return RAIZ


@pytest.fixture(scope="session")
def ejemplos(raiz: Path) -> Path:
    return raiz / "ejemplos"


@pytest.fixture(scope="session")
def pdf_bookmarks(ejemplos: Path) -> Path:
    return ejemplos / "expediente_sintetico.pdf"


@pytest.fixture(scope="session")
def pdf_texto(ejemplos: Path) -> Path:
    return ejemplos / "expediente_sin_bookmarks.pdf"


@pytest.fixture(scope="session")
def pdf_anidado(ejemplos: Path) -> Path:
    return ejemplos / "expediente_anidado.pdf"


@pytest.fixture(scope="session")
def pdf_inicial(ejemplos: Path) -> Path:
    return ejemplos / "expediente_inicial.pdf"


@pytest.fixture(scope="session")
def mapa_json(ejemplos: Path) -> Path:
    return ejemplos / "mapa_sintetico.json"


@pytest.fixture(scope="session")
def mapa_csv(ejemplos: Path) -> Path:
    return ejemplos / "mapa_sintetico.csv"


@pytest.fixture
def pdf_factory(tmp_path: Path):
    """Crea PDFs sintéticos a medida dentro de tmp_path."""

    def crear(
        nombre: str,
        paginas: list[list[str]],
        marcadores: list[tuple[int, str, int]] | None = None,
    ) -> Path:
        return crear_pdf(
            tmp_path / nombre,
            paginas=paginas,
            marcadores=marcadores,
        )

    return crear
