#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera el catálogo PDF de MK a partir de los datos de index.html.

Los productos NO se duplican aquí: se extraen del propio index.html
ejecutando su sección de datos con node, así el PDF y la web no pueden
desincronizarse.

El PDF se escribe a mano (texto vectorial con Helvetica, imágenes JPEG
incrustadas) porque en este equipo no hay reportlab ni conversores de
documentos. Ventaja: el texto queda seleccionable y buscable.

Uso:  python3 generar-catalogo.py [salida.pdf]
"""

import json
import pathlib
import re
import struct
import subprocess
import sys

import numpy as np

BASE = pathlib.Path(__file__).resolve().parent
ORIGEN = BASE / "index.html"
SALIDA = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else BASE / "catalogo.pdf"


# ─────────────────────────────────────────────────────────────────────
# 1 · Datos, leídos de index.html
# ─────────────────────────────────────────────────────────────────────

def cargar_productos():
    src = ORIGEN.read_text(encoding="utf-8")
    js = re.search(r"<script>(.*?)</script>", src, re.S).group(1)
    corte = js.index("2 · ESTADO")          # la sección 2 ya usa el DOM
    datos = js[: js.rindex("/*", 0, corte)]
    tmp = BASE / ".extraer.js"
    tmp.write_text(datos + "\nconsole.log(JSON.stringify(PRODUCTOS));\n",
                   encoding="utf-8")
    try:
        r = subprocess.run(["node", str(tmp)], capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit("node falló al leer los datos:\n" + r.stderr[:900])
        return json.loads(r.stdout.strip())
    finally:
        tmp.unlink(missing_ok=True)


# ─────────────────────────────────────────────────────────────────────
# 2 · Métricas de Helvetica (fuentes estándar del PDF, no se incrustan)
# ─────────────────────────────────────────────────────────────────────

W_REG = {
    " ":278,"!":278,'"':355,"#":556,"$":556,"%":889,"&":667,"'":191,"(":333,")":333,
    "*":389,"+":584,",":278,"-":333,".":278,"/":278,
    ":":278,";":278,"<":584,"=":584,">":584,"?":556,"@":1015,
    "[":278,"\\":278,"]":278,"^":469,"_":556,"`":333,
    "{":334,"|":260,"}":334,"~":584,
    "A":667,"B":667,"C":722,"D":722,"E":667,"F":611,"G":778,"H":722,"I":278,"J":500,
    "K":667,"L":556,"M":833,"N":722,"O":778,"P":667,"Q":778,"R":722,"S":667,"T":611,
    "U":722,"V":667,"W":944,"X":667,"Y":667,"Z":611,
    "a":556,"b":556,"c":500,"d":556,"e":556,"f":278,"g":556,"h":556,"i":222,"j":222,
    "k":500,"l":222,"m":833,"n":556,"o":556,"p":556,"q":556,"r":333,"s":500,"t":278,
    "u":556,"v":500,"w":722,"x":500,"y":500,"z":500,
}
W_BOLD = {
    " ":278,"!":333,'"':474,"#":556,"$":556,"%":889,"&":722,"'":238,"(":333,")":333,
    "*":389,"+":584,",":278,"-":333,".":278,"/":278,
    ":":333,";":333,"<":584,"=":584,">":584,"?":611,"@":975,
    "[":333,"\\":278,"]":333,"^":584,"_":556,"`":333,
    "{":389,"|":280,"}":389,"~":584,
    "A":722,"B":722,"C":722,"D":722,"E":667,"F":611,"G":778,"H":722,"I":278,"J":556,
    "K":722,"L":611,"M":833,"N":722,"O":778,"P":667,"Q":778,"R":722,"S":667,"T":611,
    "U":722,"V":667,"W":944,"X":667,"Y":667,"Z":611,
    "a":556,"b":611,"c":556,"d":611,"e":556,"f":333,"g":611,"h":611,"i":278,"j":278,
    "k":556,"l":278,"m":889,"n":611,"o":611,"p":611,"q":611,"r":389,"s":556,"t":333,
    "u":611,"v":556,"w":778,"x":556,"y":556,"z":500,
}
for _t in (W_REG, W_BOLD):
    for _c in "0123456789":
        _t[_c] = 556

ACENTOS = {
    "á":"a","é":"e","í":"i","ó":"o","ú":"u","ü":"u","ñ":"n",
    "Á":"A","É":"E","Í":"I","Ó":"O","Ú":"U","Ü":"U","Ñ":"N",
    "·":"-","—":"-","–":"-","°":"o","×":"x","€":"E",
    "«":'"',"»":'"',"“":'"',"”":'"',"‘":"'","’":"'",
}


def ancho(txt, negrita, tam):
    tabla = W_BOLD if negrita else W_REG
    return sum(tabla.get(ACENTOS.get(c, c), 556) for c in txt) * tam / 1000.0


def envolver(txt, negrita, tam, ancho_max):
    lineas, actual = [], ""
    for p in txt.split():
        prueba = (actual + " " + p).strip()
        if not actual or ancho(prueba, negrita, tam) <= ancho_max:
            actual = prueba
        else:
            lineas.append(actual)
            actual = p
    if actual:
        lineas.append(actual)
    return lineas


# ─────────────────────────────────────────────────────────────────────
# 3 · Escritor de PDF
# ─────────────────────────────────────────────────────────────────────

PW, PH = 842.0, 595.0          # A4 apaisado: fichas y ángulos
PWV, PHV = 595.0, 842.0        # A4 vertical: el índice
MARGEN = 46.0
PIE_Y = PH - 34                # línea del pie

NEGRO = (0.07, 0.07, 0.07)
GRIS = (0.44, 0.44, 0.45)
CLARO = (0.90, 0.90, 0.90)


def _esc(s):
    """Convierte a caracteres de un byte (WinAnsi) con los escapes de PDF.

    Se devuelve un str cuyos ordinales son 0-255; el flujo se serializa
    después con latin-1, de modo que cada ordinal acaba siendo un byte.
    Así '·' (0xB7) o '—' (0x97 en WinAnsi) viajan intactos.
    """
    out = []
    for ch in s:
        try:
            crudo = ch.encode("cp1252")
        except UnicodeEncodeError:
            crudo = b"?"
        for byte in crudo:
            c = chr(byte)
            if c in "()\\":
                out.append("\\" + c)
            elif byte < 32:
                out.append(" ")
            else:
                out.append(c)
    return "".join(out)


class PDF:
    def __init__(self):
        self.objetos = []          # cuerpos (bytes); número de objeto = índice+1
        self.flujos = []           # números de objeto de los /Contents
        self.imagenes = {}         # ruta -> (nombre, num, ancho_px, alto_px)

    def _nuevo(self, cuerpo):
        self.objetos.append(cuerpo)
        return len(self.objetos)

    def agregar_jpeg(self, ruta):
        ruta = str(ruta)
        if ruta in self.imagenes:
            return self.imagenes[ruta]
        datos = pathlib.Path(ruta).read_bytes()
        if datos[:2] != b"\xff\xd8":
            raise ValueError(f"{ruta} no es JPEG")
        ancho_px = alto_px = None
        i = 2
        while i < len(datos) - 9:
            if datos[i] != 0xFF:
                i += 1
                continue
            marca = datos[i + 1]
            if marca in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                         0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                alto_px, ancho_px = struct.unpack(">HH", datos[i + 5:i + 9])
                break
            if marca in (0xD8, 0xD9) or 0xD0 <= marca <= 0xD7:
                i += 2
            else:
                i += 2 + struct.unpack(">H", datos[i + 2:i + 4])[0]
        if not ancho_px:
            raise ValueError(f"no se pudieron leer las dimensiones de {ruta}")

        nombre = "Im%d" % (len(self.imagenes) + 1)
        cab = (f"<< /Type /XObject /Subtype /Image /Width {ancho_px} "
               f"/Height {alto_px} /ColorSpace /DeviceRGB /BitsPerComponent 8 "
               f"/Filter /DCTDecode /Length {len(datos)} >>")
        num = self._nuevo(cab.encode("latin-1") + b"\nstream\n" + datos
                          + b"\nendstream")
        self.imagenes[ruta] = (nombre, num, ancho_px, alto_px)
        return self.imagenes[ruta]

    def agregar_pagina(self, contenido, ancho=PW, alto=PH):
        flujo = contenido.encode("latin-1", "replace")
        num = self._nuevo(f"<< /Length {len(flujo)} >>\nstream\n".encode("latin-1")
                          + flujo + b"\nendstream")
        self.flujos.append((num, ancho, alto))

    def guardar(self, ruta, titulo="Catálogo", enlaces_por_pagina=None,
                entradas_outline=None):
        # Fuentes
        f1 = self._nuevo(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica "
                         b"/Encoding /WinAnsiEncoding >>")
        f2 = self._nuevo(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold "
                         b"/Encoding /WinAnsiEncoding >>")

        xobj = " ".join(f"/{nom} {num} 0 R"
                        for nom, num, _, _ in self.imagenes.values())

        # Enlaces internos. Se crean ANTES que las páginas porque una
        # anotación necesita el número del objeto de página de destino, y a
        # su vez las páginas necesitan los números de sus anotaciones. El
        # orden se resuelve reservando los números de página por adelantado:
        # las anotaciones ocupan exactamente n_anots objetos.
        enlaces_por_pagina = enlaces_por_pagina or []
        n_anots = sum(len(a) for a in enlaces_por_pagina)
        base_paginas = len(self.objetos) + n_anots + 1
        nums_pagina = [base_paginas + i for i in range(len(self.flujos))]

        anots = [[] for _ in nums_pagina]
        for i, lista in enumerate(enlaces_por_pagina):
            for (x1, y1, x2, y2, destino) in lista:
                cuerpo = (f"<< /Type /Annot /Subtype /Link "
                          f"/Rect [{x1:.2f} {y1:.2f} {x2:.2f} {y2:.2f}] "
                          f"/Border [0 0 0] "
                          f"/Dest [{nums_pagina[destino]} 0 R /Fit] >>")
                anots[i].append(self._nuevo(cuerpo.encode("latin-1")))

        # El objeto /Pages va después de las páginas: reservamos su número
        num_padres = len(self.objetos) + len(self.flujos) + 1
        creadas = []
        for idx, (num_flujo, pw, ph) in enumerate(self.flujos):
            ann = (" /Annots [" + " ".join(f"{a} 0 R" for a in anots[idx]) + "]"
                   if anots[idx] else "")
            cuerpo = (f"<< /Type /Page /Parent {num_padres} 0 R "
                      f"/MediaBox [0 0 {pw:.0f} {ph:.0f}] "
                      f"/Resources << /Font << /F1 {f1} 0 R /F2 {f2} 0 R >> "
                      f"/XObject << {xobj} >> >> "
                      f"/Contents {num_flujo} 0 R{ann} >>")
            creadas.append(self._nuevo(cuerpo.encode("latin-1")))
        assert creadas == nums_pagina, "desajuste al numerar las páginas"
        nums_pagina = creadas

        kids = " ".join(f"{n} 0 R" for n in nums_pagina)
        assert self._nuevo(
            f"<< /Type /Pages /Kids [{kids}] /Count {len(nums_pagina)} >>"
            .encode("latin-1")) == num_padres, "desajuste en el árbol de páginas"

        # Marcadores. Es la navegación más fiable en el móvil, porque no
        # depende de que el lector respete las anotaciones /Link del índice.
        num_outlines = None
        if entradas_outline:
            L = len(entradas_outline)
            L0 = len(self.objetos)
            num_outlines = L0 + L + 1
            nums = []
            for i, (titulo_e, pag) in enumerate(entradas_outline):
                partes = [f"/Title ({_esc(titulo_e)})",
                          f"/Parent {num_outlines} 0 R",
                          f"/Dest [{nums_pagina[pag]} 0 R /Fit]"]
                if i:
                    partes.append(f"/Prev {L0 + i} 0 R")
                if i + 1 < L:
                    partes.append(f"/Next {L0 + i + 2} 0 R")
                n = self._nuevo(("<< " + " ".join(partes) + " >>").encode("latin-1"))
                assert n == L0 + i + 1, "desajuste al numerar los marcadores"
                nums.append(n)
            # Ojo: /First y /Last son referencias indirectas, no números
            # sueltos. Sin el "0 R" los marcadores no aparecen.
            self._nuevo((f"<< /Type /Outlines /First {nums[0]} 0 R "
                         f"/Last {nums[-1]} 0 R /Count {len(nums)} >>").encode("latin-1"))

        extra_out = (f" /Outlines {num_outlines} 0 R /PageMode /UseOutlines"
                     if num_outlines else "")
        raiz = self._nuevo((f"<< /Type /Catalog /Pages {num_padres} 0 R"
                            f"{extra_out} >>").encode("latin-1"))
        info = self._nuevo(f"<< /Title ({_esc(titulo)}) "
                           f"/Creator (MK) /Producer (generar-catalogo.py) >>"
                           .encode("latin-1"))

        salida = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = [0]
        for i, cuerpo in enumerate(self.objetos, start=1):
            offsets.append(len(salida))
            salida += f"{i} 0 obj\n".encode("latin-1") + cuerpo + b"\nendobj\n"

        inicio_xref = len(salida)
        n = len(self.objetos) + 1
        salida += f"xref\n0 {n}\n".encode("latin-1")
        salida += b"0000000000 65535 f \n"
        for off in offsets[1:]:
            salida += f"{off:010d} 00000 n \n".encode("latin-1")
        salida += (f"trailer\n<< /Size {n} /Root {raiz} 0 R /Info {info} 0 R >>\n"
                   f"startxref\n{inicio_xref}\n%%EOF\n").encode("latin-1")

        pathlib.Path(ruta).write_bytes(bytes(salida))
        return len(self.flujos)


class Hoja:
    """Lienzo con coordenadas desde ARRIBA-IZQUIERDA.

    Cada hoja lleva su propio tamaño: el índice va en vertical y las fichas
    en apaisado, y las dos conviven en el mismo PDF.
    """

    def __init__(self, ancho_pag=PW, alto_pag=PH):
        self.ancho = ancho_pag
        self.alto = alto_pag
        self.ops = []
        self.enlaces = []      # (x1, y1, x2, y2, página destino)

    @property
    def pie_y(self):
        """Y de la línea del pie."""
        return self.alto - 34

    def _y(self, y):
        return self.alto - y

    def color(self, c, relleno=True):
        self.ops.append("%.3f %.3f %.3f %s" % (c[0], c[1], c[2], "rg" if relleno else "RG"))

    def texto(self, x, y, s, tam=10, negrita=False, color=NEGRO, izq=None, esp=0):
        if not s:
            return
        f = "F2" if negrita else "F1"
        if izq == "centro":
            x -= ancho(s, negrita, tam) / 2
        elif izq == "derecha":
            x -= ancho(s, negrita, tam)
        self.color(color)
        self.ops.append("BT")
        self.ops.append("/%s %.2f Tf" % (f, tam))
        self.ops.append("%.2f %.2f Td" % (x, self._y(y)))
        if esp:
            for ch in s:
                self.ops.append("(%s) Tj" % _esc(ch))
                self.ops.append("%.2f 0 Td" % esp)
        else:
            self.ops.append("(%s) Tj" % _esc(s))
        self.ops.append("ET")

    def linea(self, x1, y1, x2, y2, grosor=0.6, color=CLARO):
        self.color(color, relleno=False)
        self.ops.append("%.2f w" % grosor)
        self.ops.append("%.2f %.2f m %.2f %.2f l S"
                        % (x1, self._y(y1), x2, self._y(y2)))

    def circulo(self, cx, cy, r, relleno=None, borde=None, grosor=0.8):
        k = 0.5523 * r
        yy = self._y(cy)
        trazo = ("%.2f %.2f m %.2f %.2f %.2f %.2f %.2f %.2f c "
                 "%.2f %.2f %.2f %.2f %.2f %.2f c "
                 "%.2f %.2f %.2f %.2f %.2f %.2f c "
                 "%.2f %.2f %.2f %.2f %.2f %.2f c") % (
            cx + r, yy,
            cx + r, yy + k, cx + k, yy + r, cx, yy + r,
            cx - k, yy + r, cx - r, yy + k, cx - r, yy,
            cx - r, yy - k, cx - k, yy - r, cx, yy - r,
            cx + k, yy - r, cx + r, yy - k, cx + r, yy)
        if relleno:
            self.color(relleno)
            self.ops.append(trazo + " f")
        if borde:
            self.color(borde, relleno=False)
            self.ops.append("%.2f w" % grosor)
            self.ops.append(trazo + " S")

    def imagen(self, nombre, x, y, w, h):
        self.ops.append("q")
        self.ops.append("%.2f 0 0 %.2f %.2f %.2f cm" % (w, h, x, self._y(y + h)))
        self.ops.append("/%s Do" % nombre)
        self.ops.append("Q")

    def enlace(self, x, y, w, h, destino):
        """Zona pulsable que salta a otra página (0 = la primera).

        El rectángulo va en coordenadas PDF, que tienen el origen abajo a la
        izquierda, así que hay que darle la vuelta a la Y.
        """
        self.enlaces.append((x, self.alto - y - h,
                             x + w, self.alto - y, destino))

    def datos(self):
        return "\n".join(self.ops)


class Catalogo:
    """Gestor de páginas: permite paginar sin saber aún el total."""

    def __init__(self, pdf):
        self.pdf = pdf
        self.paginas = []

    def nueva(self, etiqueta="", ancho=PW, alto=PH):
        h = Hoja(ancho, alto)
        self.paginas.append((h, etiqueta))
        return h

    def emitir(self, titulo, entradas_outline=None):
        total = len(self.paginas)
        enlaces = []
        for i, (h, etiqueta) in enumerate(self.paginas, 1):
            footer(h, i, total, etiqueta)
            self.pdf.agregar_pagina(h.datos(), h.ancho, h.alto)
            enlaces.append(h.enlaces)
        return self.pdf.guardar(SALIDA, titulo, enlaces, entradas_outline)


def encajar(an, al, caja_w, caja_h):
    e = min(caja_w / an, caja_h / al)
    return an * e, al * e


def eur(n):
    return "S/ " + "{:,.2f}".format(n)


def footer(h, pagina, total, etiqueta=""):
    """Pie de página. Se adapta al tamaño de la hoja, porque el índice va
    en vertical y las fichas en apaisado."""
    w, y = h.ancho, h.pie_y
    h.linea(MARGEN, y, w - MARGEN, y, 0.6, CLARO)
    h.texto(MARGEN, y + 14, "MK · Catálogo", 8, False, GRIS)
    if etiqueta:
        h.texto(w / 2, y + 14, etiqueta, 8, False, GRIS, izq="centro")
    h.texto(w - MARGEN, y + 14, "%d / %d" % (pagina, total), 8, False, GRIS,
            izq="derecha")


# ─────────────────────────────────────────────────────────────────────
# 4 · Procesado de imagen: fondo blanco y sombra de contacto
# ─────────────────────────────────────────────────────────────────────

# Gancho comercial que se imprime encima de la descripción técnica. Vive
# aquí y no en index.html a propósito: el PDF puede llevar su propio texto
# de venta sin tocar los datos de la web. Si un modelo no aparece, se
# imprime solo la descripción.
GANCHOS = {
    "zapatillas-001": "Comodidad todo el día, con la pinta de un clásico.",
    "zapatillas-002": "Tres tonos de ante para quien no quiere pasar desapercibido.",
    "zapatillas-003": "Un rojo que se hace notar, con la sujeción de una caña alta.",
    "zapatillas-004": "El clásico de tres franjas, con ante que aguanta el día a día.",
    "zapatillas-005": "Rojo para destacar, sin salirse del perfil que combina con todo.",
    "zapatillas-006": "El neutro que aguanta el uso diario sin marcar.",
    "zapatillas-007": "Rojo y negro con pespunte a contraste, sobre suela gruesa.",
    "zapatillas-008": "Toda la piel, sin contraste: aquí habla el material.",
    "zapatillas-009": "Negro con pespunte crudo, para que el negro no sea aburrido.",
}

# Orden en que se agrupan los tipos en el índice y en el catálogo.
ORDEN_TIPOS = ["Caña alta", "Caña media", "Caña baja"]


def _umbrales(a, m=24):
    """Percentiles de luminancia y saturación en el marco de la foto."""
    b = np.concatenate([a[:m].reshape(-1, 3), a[-m:].reshape(-1, 3),
                        a[:, :m].reshape(-1, 3), a[:, -m:].reshape(-1, 3)]).astype(np.float32)
    lum = b.mean(axis=1); sat = b.max(axis=1) - b.min(axis=1)
    return (float(np.percentile(lum, 99)), float(np.percentile(lum, 1)),
            float(np.percentile(sat, 99)))


def _reconstruir(semilla, permitido):
    """Inundación vectorizada: crece desde `semilla` sin salir de `permitido`.

    Hace lo mismo que un relleno por inundación, pero a base de desplazar la
    máscara con numpy en vez de recorrer píxel a píxel. En una foto de 2400 px
    la diferencia es de segundos a milisegundos.
    """
    s = semilla & permitido
    while True:
        d = s.copy()
        d[1:, :] |= s[:-1, :]
        d[:-1, :] |= s[1:, :]
        d[:, 1:] |= s[:, :-1]
        d[:, :-1] |= s[:, 1:]
        d &= permitido
        if np.array_equal(d, s):
            return s
        s = d


def fondo_ya_es_blanco(im, umbral=250.0):
    """¿El fondo ya es blanco?

    Importa comprobarlo: procesar una foto que ya viene sobre blanco solo
    puede estropearla, porque la mediasuela clara se confunde con el fondo y
    el relleno se la come.
    """
    # 250 es el corte medido en esta colección: el 001 trae el fondo a 254
    # (ya blanco, no hay que tocarlo) y el 004 y el 005 a 246 (gris claro,
    # que sobre la página blanca se ve como un recuadro).
    a = np.asarray(im.convert("L").resize((140, 105))).astype(np.float32)
    m = 9
    borde = np.concatenate([a[:m].ravel(), a[-m:].ravel(),
                            a[:, :m].ravel(), a[:, -m:].ravel()])
    return float(np.median(borde)) >= umbral


def procesar_fondo(im, escala=0.35, pluma=1.0, margen=4.0, fuerza_sombra=0.35):
    """Lleva el fondo de estudio a blanco y añade una sombra de contacto.

    El fondo es un degradado gris. Se detecta por luminancia y saturación y
    se inunda desde las CUATRO ESQUINAS, de modo que las zonas claras que
    quedan encerradas dentro del zapato —la mediasuela crema— no se tocan
    aunque su color se parezca al del fondo. Los umbrales se miden en el
    propio marco de cada foto, porque cada estudio usa un gris distinto: con
    un valor fijo, el 003 perdía el borde de la mediasuela.

    Devuelve la imagen y la caja del zapato en fracciones (0-1). La caja
    hace falta para repartir las llamadas a izquierda y derecha.
    """
    from PIL import Image, ImageDraw, ImageFilter, ImageChops

    a = np.asarray(im).astype(np.float32)
    hi, lo, sb = _umbrales(a)
    tmax = hi + margen
    # Margen ajustado por abajo. Con `margen * 2` el corte quedaba en 203 y la
    # mediasuela del 007, que va de 190 a 207, entraba a medias en la máscara
    # de fondo: la mitad clara se blanqueaba y la oscura no, y salían manchas
    # grises. El fondo más oscuro de estas fotos está en 211.
    tmin = max(0.0, lo - margen * 0.5)
    tsat = max(sb + margen * 2, 10.0)
    lum = a.mean(axis=2); sat = a.max(axis=2) - a.min(axis=2)
    m = (lum > tmin) & (lum < tmax) & (sat < tsat)

    w, h = im.size
    pw, ph = max(1, int(w * escala)), max(1, int(h * escala))
    mi = Image.fromarray((m * 255).astype(np.uint8), "L").resize((pw, ph), Image.BILINEAR)
    mi = mi.point(lambda v: 255 if v > 127 else 0)
    permitido = np.asarray(mi) > 0

    # Barrera de bordes: el relleno no cruza un cambio fuerte de luminancia.
    # Es la segunda red de seguridad, para cuando el color de la suela y el
    # del fondo se solapan: el borde de la suela sí es un cambio fuerte.
    gris = np.asarray(im.convert("L").resize((pw, ph), Image.BILINEAR)).astype(np.float32)
    gy, gx = np.gradient(gris)
    mag = np.hypot(gx, gy)
    mm = 24
    borde_marco = np.concatenate([mag[:mm].ravel(), mag[-mm:].ravel(),
                                  mag[:, :mm].ravel(), mag[:, -mm:].ravel()])
    tb = max(2.5, float(np.percentile(borde_marco, 99.5)) * 2.5)
    permitido &= mag <= tb

    semilla = np.zeros_like(permitido)
    semilla[0, :] |= permitido[0, :]
    semilla[-1, :] |= permitido[-1, :]
    semilla[:, 0] |= permitido[:, 0]
    semilla[:, -1] |= permitido[:, -1]
    al = Image.fromarray((_reconstruir(semilla, permitido) * 255).astype(np.uint8), "L")
    al = al.resize((w, h), Image.BILINEAR).filter(ImageFilter.GaussianBlur(pluma))
    alpha = np.asarray(al).astype(np.float32)[..., None] / 255.0

    out = a * (1 - alpha) + 255.0 * alpha

    # Sombra de contacto: la silueta desplazada hacia abajo y difusa,
    # aplicada solo FUERA del zapato para no ensuciar el material.
    sil = 1.0 - alpha[..., 0]
    sh = Image.fromarray((np.clip(sil, 0, 1) * 255).astype(np.uint8), "L")
    sh = sh.filter(ImageFilter.GaussianBlur(max(3.0, h * 0.012)))
    sh = ImageChops.offset(sh, 0, int(h * 0.010))
    sm = np.asarray(sh).astype(np.float32) / 255.0
    # Fuera de la silueta: es una sombra proyectada, no un sombreado
    out = out * (1.0 - (sm * (1.0 - sil) * fuerza_sombra)[..., None])

    ys, xs = np.where(sil[::8, ::8] > 0.5)
    caja = ((xs.min() * 8 / w, ys.min() * 8 / h,
             xs.max() * 8 / w, ys.max() * 8 / h) if len(xs) else (0.0, 0.0, 1.0, 1.0))
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)), caja


# ─────────────────────────────────────────────────────────────────────
# 5 · Páginas
# ─────────────────────────────────────────────────────────────────────

def separar(valores, minimo, lo, hi):
    """Separa una lista de posiciones para que no se solapen, sin salirse
    del intervalo [lo, hi]."""
    v = sorted(valores)
    for i in range(1, len(v)):
        v[i] = max(v[i], v[i - 1] + minimo)
    if v and v[-1] > hi:
        v[-1] = hi
        for i in range(len(v) - 2, -1, -1):
            v[i] = min(v[i], v[i + 1] - minimo)
    return [max(lo, x) for x in v]


def ficha(cat, p, img):
    """Una página por modelo.

    La fotografía va centrada y las piezas se señalan con una llamada: un
    punto sobre la pieza y una línea hasta su etiqueta. Las etiquetas se
    reparten en dos columnas, una a cada lado, ordenadas de arriba abajo para
    que las líneas se crucen lo menos posible.
    """
    h = cat.nueva(p["nombre"])

    # Cabecera
    h.texto(MARGEN, 56, p["nombre"], 20, True, NEGRO)
    h.texto(MARGEN, 74, p["categoria"] + "  ·  " + p.get("tipo", ""), 9.5, False, GRIS)
    h.texto(PW - MARGEN, 56, eur(p["precio"]), 17, True, NEGRO, izq="derecha")
    h.texto(PW - MARGEN, 74, "%d color%s" % (p["colores"],
             "es" if p["colores"] != 1 else ""), 9.5, False, GRIS, izq="derecha")
    h.linea(MARGEN, 88, PW - MARGEN, 88, 1.1, NEGRO)

    # Gancho comercial y, debajo, la descripción técnica
    y = 106.0
    gancho = GANCHOS.get(p["id"])
    if gancho:
        for ln in envolver(gancho, True, 12, PW - 2 * MARGEN):
            h.texto(MARGEN, y, ln, 12, True, NEGRO)
            y += 15.0
        y += 4
    for ln in envolver(p.get("descripcion", ""), False, 9, PW - 2 * MARGEN):
        h.texto(MARGEN, y, ln, 9, False, (0.32, 0.32, 0.33))
        y += 12.0
    h.linea(MARGEN, y + 6, PW - MARGEN, y + 6, 0.6, CLARO)

    # Fotografía a la izquierda, lo más grande que quepa. Antes iba centrada
    # con llamadas a los dos lados, pero eso comía mucho ancho y dejaba la
    # foto pequeña: con el desglose en una sola columna, la imagen gana un
    # tercio de tamaño.
    top = y + 20
    disp = h.pie_y - 12 - top
    caja_w = PW - 2 * MARGEN - 240.0 - 26.0
    w, hh = encajar(p["w"], p["h"], caja_w, disp)
    x = MARGEN
    yy = top + (disp - hh) / 2
    h.imagen(img["nombre"], x, yy, w, hh)

    # Desglose de piezas, en una columna a la derecha
    lx = MARGEN + caja_w + 26.0
    ancho_col = PW - MARGEN - lx
    h.texto(lx, top + 2, "DESGLOSE DE PIEZAS", 8.5, True, GRIS)
    h.linea(lx, top + 10, PW - MARGEN, top + 10, 0.6, CLARO)

    paso = (disp - 26) / max(1, len(p["piezas"]))
    yl = top + 30
    for q in p["piezas"]:
        h.texto(lx, yl, q["label"], 9.5, True, NEGRO)
        sub = q["material"] + "  ·  " + q["tipo"]
        lineas = envolver(sub, False, 8.0, ancho_col)
        h.texto(lx, yl + 11.5,
                lineas[0] if len(lineas) == 1 else lineas[0][:-1] + "\u2026",
                8.0, False, GRIS)
        yl += paso
    return h


def angulos(cat, p, img):
    """Página de vistas adicionales. Opcional: solo si el producto trae la
    clave "angulos" con la ruta de un collage.

    Va justo detrás de la ficha, de modo que cada zapatilla puede tener las
    páginas extra que necesite sin afectar a las demás.
    """
    h = cat.nueva(p["nombre"] + " · ángulos")
    h.texto(MARGEN, 60, p["nombre"], 20, True, NEGRO)
    h.texto(MARGEN, 78, "Vistas adicionales", 9.5, False, GRIS)
    h.linea(MARGEN, 92, PW - MARGEN, 92, 1.1, NEGRO)

    caja_w, caja_h = PW - 2 * MARGEN, 414.0
    w, hh = encajar(img["w"], img["h"], caja_w, caja_h)
    h.imagen(img["nombre"], MARGEN + (caja_w - w) / 2,
             106 + (caja_h - hh) / 2, w, hh)

    h.texto(PW / 2, 106 + caja_h + 24,
            "Perfil  ·  Tres cuartos frontal  ·  Tres cuartos trasero  ·  "
            "Vista superior  ·  Planta  ·  Trasera",
            8.5, False, GRIS, izq="centro")
    return h


# ─────────────────────────────────────────────────────────────────────
# 6 · Programa
# ─────────────────────────────────────────────────────────────────────

LADO_MAX = 1900      # el JPEG incrustado no necesita más que esto
BLANQUEAR_FONDO = True   # False para incrustar las fotos tal cual

# Precio que se imprime en el catálogo. Va aparte a propósito: así el PDF
# puede llevar un precio distinto al de la web sin tocar index.html.
# Pon None para que use el precio de la web.
PRECIO_CATALOGO = 110.0


def ordenar_por_tipo(productos):
    """Agrupa por tipo respetando el orden de ORDEN_TIPOS.

    sorted() es estable, así que dentro de cada tipo los modelos conservan
    el orden en que están en index.html.
    """
    def clave(p):
        t = p.get("tipo", "")
        return ORDEN_TIPOS.index(t) if t in ORDEN_TIPOS else len(ORDEN_TIPOS)
    return sorted(productos, key=clave)


ALTO_FILA = 62.0        # alto de cada fila del índice
ALTO_ENC = 34.0         # alto del encabezado de tipo, con su aire
TOPE_IND = 118.0        # primera Y útil tras la cabecera del índice


def repartir_indice(productos):
    """Reparte el índice en páginas antes de dibujarlo.

    Hace falta porque el número de páginas del índice condiciona en qué
    página empieza cada modelo, y a su vez el índice imprime ese número.
    Se resuelve simulando el reparto con aritmética, sin tocar el PDF.

    Devuelve una lista de páginas; cada una es una lista de
    (encabezado o None, producto).
    """
    tope = PHV - 34 - 14
    paginas, actual, y, tipo = [], [], TOPE_IND, None
    for p in productos:
        t = p.get("tipo", "")
        enc, alto = None, ALTO_FILA
        if t != tipo:
            enc, tipo = t, t
            alto += ALTO_ENC
        # si no cabe, página nueva repitiendo el encabezado del tipo
        if y + alto > tope and actual:
            paginas.append(actual)
            actual, y = [], TOPE_IND
            if enc is None:
                enc, alto = t, ALTO_FILA + ALTO_ENC
        actual.append((enc, p))
        y += alto
    if actual:
        paginas.append(actual)
    return paginas


def indice(cat, productos, paginas, minis):
    """Índice de modelos, en VERTICAL y agrupado por tipo.

    Va en vertical a propósito: en el móvil una página apaisada obliga a
    girar el teléfono, y este índice es la puerta de entrada al catálogo.
    Cada fila es una zona pulsable que salta a la ficha del modelo.

    Se reparte solo en varias páginas si hace falta: con nueve modelos cabe
    en una, pero añadir más no lo rompe.
    """
    reparto = repartir_indice(productos)
    for n_pag, filas in enumerate(reparto):
        h = cat.nueva("Índice" if n_pag == 0 else "Índice · continuación",
                      PWV, PHV)
        W = h.ancho
        util = W - 2 * MARGEN
        if n_pag == 0:
            h.texto(MARGEN, 62, "Índice", 22, True, NEGRO)
            h.texto(MARGEN, 81, "Colección completa, agrupada por tipo de caña",
                    9.5, False, GRIS)
            h.linea(MARGEN, 96, W - MARGEN, 96, 1.1, NEGRO)
        else:
            h.texto(MARGEN, 62, "Índice", 22, True, NEGRO)
            h.texto(MARGEN, 81, "continuación", 9.5, False, GRIS)
            h.linea(MARGEN, 96, W - MARGEN, 96, 1.1, NEGRO)

        y = TOPE_IND
        for enc, q in filas:
            if enc is not None:
                if y > TOPE_IND:
                    y += 12          # aire entre grupos
                h.texto(MARGEN, y, enc.upper(), 8.5, True, GRIS)
                h.linea(MARGEN, y + 6, W - MARGEN, y + 6, 0.6, CLARO)
                y += ALTO_ENC

            cw, ch = 96.0, 54.0
            nom, aw, ah = minis[q["id"]][:3]
            w, hh = encajar(aw, ah, cw, ch)
            h.imagen(nom, MARGEN + (cw - w) / 2, y + (ch - hh) / 2, w, hh)

            tx = MARGEN + cw + 16
            h.texto(tx, y + 24, q["nombre"], 12.5, True, NEGRO)
            h.texto(tx, y + 40, "%s  ·  %d color%s" % (
                q["categoria"], q["colores"],
                "es" if q["colores"] != 1 else ""), 8.5, False, GRIS)
            h.texto(500, y + 24, eur(q["precio"]), 11, True, NEGRO, izq="derecha")
            h.texto(W - MARGEN, y + 24, "pág. %d" % paginas[q["id"]],
                    9.5, False, GRIS, izq="derecha")
            h.linea(MARGEN, y + ALTO_FILA - 6, W - MARGEN, y + ALTO_FILA - 6,
                    0.5, CLARO)

            h.enlace(MARGEN, y - 4, util, ALTO_FILA, paginas[q["id"]] - 1)
            y += ALTO_FILA
    return len(reparto)


def preparar(pdf, ruta, clave, temporales, Image, fondo=True):
    """Procesa, guarda como JPEG temporal e incrusta la imagen.

    Un temporal por imagen: agregar_jpeg cachea por ruta, así que reutilizar
    el mismo nombre haría que un modelo saliera con la foto de otro.
    """
    im = Image.open(ruta).convert("RGB")
    caja = (0.0, 0.0, 1.0, 1.0)
    if fondo and BLANQUEAR_FONDO and not fondo_ya_es_blanco(im):
        im, caja = procesar_fondo(im)
    if max(im.size) > LADO_MAX:
        e = LADO_MAX / max(im.size)
        im = im.resize((round(im.width * e), round(im.height * e)), Image.LANCZOS)
    tmp = BASE / (".catalogo-%s.jpg" % clave)
    im.save(tmp, "JPEG", quality=86, optimize=True, progressive=False)
    temporales.append(tmp)
    nombre, _, _, _ = pdf.agregar_jpeg(tmp)
    return nombre, im.width, im.height, caja


def main():
    productos = cargar_productos()
    if not productos:
        raise SystemExit("no hay productos en index.html")

    if PRECIO_CATALOGO is not None:
        productos = [dict(p, precio=PRECIO_CATALOGO) for p in productos]
    productos = ordenar_por_tipo(productos)

    try:
        from PIL import Image
    except ImportError:
        raise SystemExit("se necesita Pillow para preparar las imágenes")

    pdf = PDF()
    cat = Catalogo(pdf)
    temporales = []

    # Primero TODAS las imágenes: el índice necesita las miniaturas y hay
    # que saber en qué página empieza cada modelo antes de escribir el índice.
    minis = {}
    for p in productos:
        nombre, aw, ah, caja = preparar(pdf, BASE / p["img"], p["id"],
                                        temporales, Image)
        minis[p["id"]] = (nombre, aw, ah, caja)

    # El índice puede ocupar varias páginas, y los modelos empiezan después.
    # Se simula el reparto antes de numerar nada.
    n_indice = len(repartir_indice(productos))
    paginas = {}
    n = 1 + n_indice
    for p in productos:
        paginas[p["id"]] = n
        n += 1 + (1 if p.get("angulos") else 0)

    indice(cat, productos, paginas, minis)

    for p in productos:
        nombre, _, _, caja = minis[p["id"]]
        ficha(cat, p, {"nombre": nombre, "caja": caja})
        if p.get("angulos"):
            # El collage ya viene sobre blanco: no se le toca el fondo.
            nombre2, aw2, ah2, _ = preparar(pdf, BASE / p["angulos"],
                                            p["id"] + "-ang", temporales,
                                            Image, fondo=False)
            angulos(cat, p, {"nombre": nombre2, "w": aw2, "h": ah2})

    for t in temporales:
        t.unlink(missing_ok=True)
    marcadores = [("Índice", 0)] + [(q["nombre"], paginas[q["id"]] - 1)
                                    for q in productos]
    n = cat.emitir("Catálogo MK", marcadores)
    kb = SALIDA.stat().st_size / 1024
    extra = sum(1 for p in productos if p.get("angulos"))
    print("PDF generado: %s" % SALIDA)
    print("  %d página(s) · %.0f KB · %d producto(s) · %d con ángulos"
          % (n, kb, len(productos), extra))


if __name__ == "__main__":
    main()
