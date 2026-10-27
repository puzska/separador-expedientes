"""Tests de los archivos de ejemplo y de su carácter ficticio."""

from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader

from generar_ejemplo import generar


def test_los_ejemplos_se_pueden_regenerar(tmp_path, raiz):
    generados = generar(tmp_path)

    assert len(generados) == 6
    for ruta in generados:
        esperado = raiz / "ejemplos" / ruta.name
        assert esperado.exists(), f"Falta el ejemplo {esperado.name}"
        assert ruta.read_bytes() == esperado.read_bytes(), (
            f"{esperado.name} está desactualizado: "
            "ejecutá python scripts/generar_ejemplo.py"
        )


def test_todos_los_pdfs_son_ficticios(ejemplos: Path):
    pdfs = sorted(ejemplos.glob("*.pdf"))
    assert len(pdfs) == 4

    for pdf in pdfs:
        lector = PdfReader(str(pdf))
        assert len(lector.pages) > 0
        for numero, pagina in enumerate(lector.pages, 1):
            texto = pagina.extract_text() or ""
            assert "EJEMPLO FICTICIO - SIN DATOS REALES" in texto, (
                f"{pdf.name}, página {numero}: falta la leyenda de ejemplo "
                "ficticio"
            )
