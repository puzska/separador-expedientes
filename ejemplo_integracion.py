"""Ejemplo de uso del separador como módulo.

Uso::

    python ejemplo_integracion.py
    python ejemplo_integracion.py "C:\\ruta\\expediente.pdf"
    python ejemplo_integracion.py "C:\\ruta\\expediente.pdf" "C:\\ruta\\salida"
    python ejemplo_integracion.py "C:\\ruta\\expediente.pdf" "C:\\ruta\\salida" --dividir

Sin argumentos usa ``ejemplos/expediente_sintetico.pdf``, un PDF ficticio
incluido en el repositorio. Sin ``--dividir`` solo muestra la detección y no
escribe archivos.
"""

from __future__ import annotations

import sys
from pathlib import Path

from separador_expediente import detectar_tramites, dividir_expediente

BASE = Path(__file__).resolve().parent
EJEMPLO = BASE / "ejemplos" / "expediente_sintetico.pdf"


def main() -> int:
    argumentos = [a for a in sys.argv[1:] if a != "--dividir"]
    dividir = "--dividir" in sys.argv[1:]

    if argumentos:
        pdf = Path(argumentos[0])
    else:
        pdf = EJEMPLO

    if not pdf.exists():
        print(f"ERROR: no existe el PDF: {pdf}", file=sys.stderr)
        return 2

    salida = (
        Path(argumentos[1])
        if len(argumentos) > 1
        else BASE / "salida_ejemplo"
    )

    if pdf == EJEMPLO:
        print(f"Usando el ejemplo ficticio: {pdf.name}\n")

    tramites = detectar_tramites(pdf, agrupar="fecha", modo="auto")
    print(f"Trámites detectados: {len(tramites)}")
    for tramite in tramites[:10]:
        print(
            f"  {tramite.paginas:>10}  "
            f"{tramite.categoria:<45}  {tramite.nombre}"
        )
    if len(tramites) > 10:
        print(f"  ... y {len(tramites) - 10} más")

    if not dividir:
        print(
            "\nNo se generaron archivos. "
            "Agregá --dividir para separar los PDFs."
        )
        return 0

    resultado = dividir_expediente(
        pdf,
        salida,
        tramites,
        prefijo=f"{pdf.stem}_",
    )
    print(f"\nGenerados {len(resultado)} PDFs en: {salida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
