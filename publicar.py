#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prepara `docs/` con lo que se publica en GitHub Pages.

Solo se copia la web: `index.html` y `img/`. Los PDF, los scripts, la hoja de
revisión de materiales y la imagen de verificación se quedan fuera, porque no
tienen nada que hacer en un sitio público.

Se publica desde una carpeta `docs/` en vez de la raíz para no arrastrar el
resto del proyecto. GitHub Pages sabe servir desde ahí.

Uso:  python3 publicar.py
"""

import pathlib
import shutil

BASE = pathlib.Path(__file__).resolve().parent
DEST = BASE / "docs"

PUBLICAR = ["index.html", "img"]


def main():
    if DEST.exists():
        shutil.rmtree(DEST)
    DEST.mkdir()

    for nombre in PUBLICAR:
        origen = BASE / nombre
        if not origen.exists():
            raise SystemExit("falta %s" % origen)
        if origen.is_dir():
            shutil.copytree(origen, DEST / nombre)
        else:
            shutil.copy2(origen, DEST / nombre)

    # Sin esto, GitHub Pages pasa los archivos por Jekyll, que ignora los que
    # empiezan por guion bajo y puede reescribir cosas sin avisar.
    (DEST / ".nojekyll").touch()

    archivos = [f for f in DEST.rglob("*") if f.is_file()]
    kb = sum(f.stat().st_size for f in archivos) / 1024
    print("docs/ listo: %d archivos · %.0f KB" % (len(archivos), kb))
    for f in sorted(archivos):
        print("   %s" % f.relative_to(BASE))


if __name__ == "__main__":
    main()
