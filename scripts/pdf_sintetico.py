"""Generador mínimo de PDFs sintéticos para ejemplos y tests.

No usa ninguna librería externa: escribe el PDF a mano. Todo el contenido es
inventado y lleva la leyenda "EJEMPLO FICTICIO - SIN DATOS REALES" en cada
página.

Uso desde código::

    from pdf_sintetico import crear_pdf

    crear_pdf(
        "salida.pdf",
        paginas=[["Linea 1", "Linea 2"]],
        marcadores=[(1, "01/01/2025 - DEMANDA", 1)],
    )

``marcadores`` es una lista de ``(nivel, titulo, pagina)``. El nivel 1 es el
más superficial; un nivel mayor se anida dentro del anterior.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

LEYENDA = "EJEMPLO FICTICIO - SIN DATOS REALES"


def _cadena_pdf(texto: str) -> bytes:
    """Codifica un string PDF escapando los caracteres especiales."""
    datos = str(texto).encode("latin-1", "replace")
    datos = (
        datos.replace(b"\\", b"\\\\")
        .replace(b"(", b"\\(")
        .replace(b")", b"\\)")
    )
    return b"(" + datos + b")"


def _contenido_pagina(lineas: Sequence[str]) -> bytes:
    partes = [b"BT", b"/F1 11 Tf", b"16 TL", b"60 790 Td"]
    for indice, linea in enumerate(lineas):
        if indice:
            partes.append(b"T*")
        partes.extend((_cadena_pdf(linea), b"Tj"))
    partes.extend(
        (
            b"ET",
            b"BT",
            b"/F1 8 Tf",
            b"60 40 Td",
            _cadena_pdf(LEYENDA),
            b"Tj",
            b"ET",
        )
    )
    return b"\n".join(partes)


def _construir_arbol(
    marcadores: Iterable[tuple[int, str, int]],
) -> list[dict]:
    raices: list[dict] = []
    pila: list[tuple[int, dict]] = []
    for nivel, titulo, pagina in marcadores:
        nodo = {
            "nivel": int(nivel),
            "titulo": str(titulo),
            "pagina": int(pagina),
            "hijos": [],
            "padre_num": 4,
        }
        while pila and pila[-1][0] >= nodo["nivel"]:
            pila.pop()
        if pila:
            padre = pila[-1][1]
            nodo["padre_num"] = None  # se completa al numerar
            padre["hijos"].append(nodo)
        else:
            raices.append(nodo)
        pila.append((nodo["nivel"], nodo))
    return raices


def _numerar(raices: Sequence[dict], inicio: int) -> tuple[list[dict], int]:
    orden: list[dict] = []
    siguiente = inicio

    def recorrer(nodos: Sequence[dict], padre_num: int) -> None:
        nonlocal siguiente
        for nodo in nodos:
            nodo["num"] = siguiente
            nodo["padre_num"] = padre_num
            siguiente += 1
            orden.append(nodo)
            recorrer(nodo["hijos"], nodo["num"])

    recorrer(raices, 4)
    return orden, siguiente


def _contar_descendientes(nodo: dict) -> int:
    return len(nodo["hijos"]) + sum(
        _contar_descendientes(hijo) for hijo in nodo["hijos"]
    )


def _enlazar_hermanos(nodos: Sequence[dict]) -> None:
    for indice, nodo in enumerate(nodos):
        nodo["prev"] = nodos[indice - 1]["num"] if indice else None
        nodo["next"] = nodos[indice + 1]["num"] if indice + 1 < len(nodos) else None
        _enlazar_hermanos(nodo["hijos"])


def _objeto_outline(nodo: dict) -> bytes:
    partes = [
        b"<< /Title " + _cadena_pdf(nodo["titulo"]),
        b"/Parent " + str(nodo["padre_num"]).encode() + b" 0 R",
        b"/Dest [" + str(nodo["pagina_obj"]).encode() + b" 0 R /Fit]",
    ]
    if nodo["prev"] is not None:
        partes.append(b"/Prev " + str(nodo["prev"]).encode() + b" 0 R")
    if nodo["next"] is not None:
        partes.append(b"/Next " + str(nodo["next"]).encode() + b" 0 R")
    if nodo["hijos"]:
        partes.append(b"/First " + str(nodo["hijos"][0]["num"]).encode() + b" 0 R")
        partes.append(b"/Last " + str(nodo["hijos"][-1]["num"]).encode() + b" 0 R")
        partes.append(
            b"/Count " + str(_contar_descendientes(nodo)).encode()
        )
    partes.append(b">>")
    return b" ".join(partes)


def _escribir_pdf(ruta: Path, objetos: dict[int, bytes]) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    salida = bytearray(b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n")
    offsets: dict[int, int] = {}
    for numero in sorted(objetos):
        offsets[numero] = len(salida)
        salida += f"{numero} 0 obj\n".encode()
        salida += objetos[numero]
        salida += b"\nendobj\n"

    inicio_xref = len(salida)
    total = max(objetos) + 1
    salida += f"xref\n0 {total}\n".encode()
    salida += b"0000000000 65535 f \n"
    for numero in range(1, total):
        offset = offsets.get(numero)
        if offset is None:
            salida += b"0000000000 65535 f \n"
        else:
            salida += f"{offset:010d} 00000 n \n".encode()
    salida += (
        f"trailer\n<< /Size {total} /Root 1 0 R >>\n"
        f"startxref\n{inicio_xref}\n%%EOF\n"
    ).encode()
    ruta.write_bytes(bytes(salida))


def crear_pdf(
    ruta: str | Path,
    *,
    paginas: Sequence[Sequence[str]],
    marcadores: Sequence[tuple[int, str, int]] | None = None,
) -> Path:
    """Crea un PDF con texto y, opcionalmente, un índice de bookmarks."""
    ruta = Path(ruta)
    if not paginas:
        raise ValueError("El PDF necesita al menos una página.")

    marcadores = list(marcadores or [])
    total_paginas = len(paginas)
    for nivel, _titulo, pagina in marcadores:
        if int(nivel) < 1:
            raise ValueError("El nivel de un marcador debe ser >= 1.")
        if not 1 <= int(pagina) <= total_paginas:
            raise ValueError(
                f"El marcador apunta a la página {pagina}, "
                f"fuera del rango 1-{total_paginas}."
            )

    con_outline = bool(marcadores)
    primera_pagina = 5 if con_outline else 4
    objetos: dict[int, bytes] = {}

    catalogo = b"<< /Type /Catalog /Pages 2 0 R"
    if con_outline:
        catalogo += b" /Outlines 4 0 R /PageMode /UseOutlines"
    objetos[1] = catalogo + b" >>"

    kids = b" ".join(
        f"{primera_pagina + 2 * indice + 1} 0 R".encode()
        for indice in range(total_paginas)
    )
    objetos[2] = (
        b"<< /Type /Pages /Kids [" + kids + b"] /Count "
        + str(total_paginas).encode()
        + b" >>"
    )
    objetos[3] = (
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica "
        b"/Encoding /WinAnsiEncoding >>"
    )

    for indice, lineas in enumerate(paginas):
        contenido = _contenido_pagina(lineas)
        num_contenido = primera_pagina + 2 * indice
        num_pagina = num_contenido + 1
        objetos[num_contenido] = (
            b"<< /Length "
            + str(len(contenido)).encode()
            + b" >>\nstream\n"
            + contenido
            + b"\nendstream"
        )
        objetos[num_pagina] = (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            b"/Resources << /Font << /F1 3 0 R >> >> /Contents "
            + str(num_contenido).encode()
            + b" 0 R >>"
        )

    if con_outline:
        raices = _construir_arbol(marcadores)
        orden, _siguiente = _numerar(
            raices, primera_pagina + 2 * total_paginas
        )
        for nodo in orden:
            nodo["pagina_obj"] = (
                primera_pagina + 2 * (nodo["pagina"] - 1) + 1
            )
        _enlazar_hermanos(raices)
        objetos[4] = (
            b"<< /Type /Outlines /First "
            + str(raices[0]["num"]).encode()
            + b" 0 R /Last "
            + str(raices[-1]["num"]).encode()
            + b" 0 R /Count "
            + str(len(orden)).encode()
            + b" >>"
        )
        for nodo in orden:
            objetos[nodo["num"]] = _objeto_outline(nodo)

    _escribir_pdf(ruta, objetos)
    return ruta
