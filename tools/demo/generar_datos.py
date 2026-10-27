"""Genera los datos del demo a partir de la salida real del CLI.

El demo usa el PDF sintético de ``ejemplos/`` y muestra la salida real de
``--listar`` y de una división. Después reemplaza las rutas temporales por una
ruta ficticia para que el GIF no dependa de la máquina donde se generó.

Uso::

    python tools/demo/generar_datos.py

Escribe ``tools/demo/datos.js``.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
PDF_EJEMPLO = RAIZ / "ejemplos" / "expediente_sintetico.pdf"
SCRIPT = RAIZ / "separador_expediente.py"
SALIDA_DATOS = Path(__file__).resolve().parent / "datos.js"

RUTA_DEMO = r"C:\casos\expediente-demo"
NOMBRE_SALIDA = "TRAMITES SEPARADOS"


def _ejecutar(argumentos: list[str], cwd: Path) -> str:
    proceso = subprocess.run(
        [sys.executable, str(SCRIPT), *argumentos],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if proceso.returncode != 0:
        raise SystemExit(
            "El CLI falló al generar el demo:\n"
            f"{proceso.stdout}\n{proceso.stderr}"
        )
    return proceso.stdout


def _recortar_hasta_indice(lineas: list[str]) -> list[str]:
    """Quita la tabla final que el CLI imprime después del índice."""
    recortadas: list[str] = []
    for linea in lineas:
        recortadas.append(linea)
        if linea.startswith("Índice:"):
            break
    return recortadas


def generar() -> dict:
    with tempfile.TemporaryDirectory(prefix="separador_demo_") as temporal:
        cwd = Path(temporal)
        shutil.copyfile(PDF_EJEMPLO, cwd / "expediente.pdf")

        listar = _ejecutar(["expediente.pdf", "--listar"], cwd)
        dividir = _ejecutar(
            ["expediente.pdf", "-o", NOMBRE_SALIDA],
            cwd,
        )

        carpeta_salida = (cwd / NOMBRE_SALIDA).resolve()
        ruta_ficticia = RUTA_DEMO + "\\" + NOMBRE_SALIDA

        lineas_dividir = _recortar_hasta_indice(
            dividir.rstrip("\n").splitlines()
        )
        lineas_dividir = [
            linea.replace(str(carpeta_salida), ruta_ficticia)
            for linea in lineas_dividir
        ]

        archivos = sorted(
            ruta.name for ruta in (cwd / NOMBRE_SALIDA).iterdir()
        )

    return {
        "prompt": RUTA_DEMO + ">",
        "listar": {
            "comando": "separador-expedientes expediente.pdf --listar",
            "salida": listar.rstrip("\n").splitlines(),
        },
        "dividir": {
            "comando": (
                'separador-expedientes expediente.pdf -o "'
                + NOMBRE_SALIDA
                + '"'
            ),
            "salida": lineas_dividir,
        },
        "archivos": {
            "comando": 'Get-ChildItem "' + NOMBRE_SALIDA + '" -Name',
            "salida": archivos,
        },
    }


def main() -> int:
    datos = generar()
    contenido = (
        "// Generado por tools/demo/generar_datos.py. Datos ficticios.\n"
        "window.DEMO_DATA = "
        + json.dumps(datos, ensure_ascii=False, indent=2)
        + ";\n"
    )
    with open(SALIDA_DATOS, "w", encoding="utf-8", newline="\n") as archivo:
        archivo.write(contenido)
    print(f"Generado: {SALIDA_DATOS.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
