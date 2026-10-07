#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deja en `img/` las fotos ya limpias: fondo blanco y sombra de contacto.

Antes esto lo hacía el generador del PDF al vuelo, así que la web servía las
fotos crudas y cada una tenía un fondo distinto (del 211 al 254 de gris). Al
hacerlo antes, la web y el PDF enseñan exactamente la misma imagen.

Los originales no se tocan: se leen de la carpeta de material y el resultado
se escribe en `img/`.

Uso:  python3 preparar-imagenes.py
"""

import importlib.util
import pathlib
import sys

sys.dont_write_bytecode = True

BASE = pathlib.Path(__file__).resolve().parent
ORIGEN = pathlib.Path("/home/josfx/Imágenes/zapatillas MK")
IMG = BASE / "img"


def motor():
    spec = importlib.util.spec_from_file_location("m", BASE / "generar-catalogo.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    m = motor()
    from PIL import Image

    if not ORIGEN.is_dir():
        raise SystemExit("no encuentro la carpeta de originales: %s" % ORIGEN)

    print(f"  {'imagen':<34}{'fondo antes':>12}{'despues':>9}   tratamiento")
    print("  " + "-" * 74)
    for destino in sorted(IMG.iterdir()):
        cand = [f for f in ORIGEN.rglob(destino.stem + ".*") if f.is_file()]
        if not cand:
            print(f"  {destino.name:<34}{'—':>12}{'—':>9}   sin original, se deja")
            continue
        origen = cand[0]
        im = Image.open(origen).convert("RGB")
        ya = m.fondo_ya_es_blanco(im)
        antes = m._umbrales(__import__("numpy").asarray(im).astype("float32"))[1]

        limpia, _ = m.procesar_fondo(im, blanquear=not ya)

        # el PNG del 001 se queda en PNG: la web lo referencia así
        if destino.suffix.lower() == ".png":
            limpia.save(destino, "PNG", optimize=True)
        else:
            limpia.save(destino, "JPEG", quality=88, optimize=True)

        print(f"  {destino.name:<34}{antes:>12.0f}{255:>9}   "
              f"{'solo sombra (ya era blanco)' if ya else 'blanquea + sombra'}")

    print("\n  img/ actualizado")


if __name__ == "__main__":
    main()
