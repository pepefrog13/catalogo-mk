#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera la guía de cuidado del ante y la gamuza en PDF.

Va aparte del catálogo y reutiliza su motor de PDF (mismas fuentes, mismo
estilo), pero no toca nada de `index.html` ni de `catalogo.pdf`.

El documento va en A4 VERTICAL: es un texto, y en vertical se lee mejor
tanto en papel como en el móvil.

Uso:  python3 generar-guia.py [salida.pdf]
"""

import importlib.util
import pathlib
import sys

sys.dont_write_bytecode = True          # no dejar __pycache__

BASE = pathlib.Path(__file__).resolve().parent
SALIDA = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else BASE / "guia-cuidado-gamuza.pdf"


def cargar_motor():
    """Importa el generador del catálogo para reutilizar su motor de PDF."""
    spec = importlib.util.spec_from_file_location("motor", BASE / "generar-catalogo.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


M = cargar_motor()

PW, PH = M.PWV, M.PHV          # A4 vertical
MARGEN = 52.0
ANCHO = PW - 2 * MARGEN

NEGRO, GRIS, CLARO = M.NEGRO, M.GRIS, M.CLARO
SUAVE = (0.30, 0.30, 0.31)
REGLA = (0.78, 0.78, 0.79)


# ─────────────────────────────────────────────────────────────────────
# Utilidades de maquetación
# ─────────────────────────────────────────────────────────────────────

def hoja(cat, etiqueta):
    """Crea una hoja A4 vertical.

    Hay que pasar el tamaño explícitamente: Catalogo.nueva usa por defecto el
    del módulo del catálogo, que es apaisado.
    """
    return cat.nueva(etiqueta, PW, PH)


def parrafo(h, y, texto, tam=9.5, color=SUAVE, w=ANCHO, interlineado=13.2):
    """Escribe un párrafo y devuelve la Y siguiente."""
    for ln in M.envolver(texto, False, tam, w):
        h.texto(MARGEN, y, ln, tam, False, color)
        y += interlineado
    return y


def rotulo(h, y, texto):
    """Encabezado de sección, en mayúsculas pequeñas."""
    h.texto(MARGEN, y, texto.upper(), 8.5, True, GRIS)
    h.linea(MARGEN, y + 7, PW - MARGEN, y + 7, 0.6, CLARO)
    return y + 22


def titulo(h, y, texto, tam=17):
    h.texto(MARGEN, y, texto, tam, True, NEGRO)
    return y + tam * 0.95 + 8


def vinetas(h, y, elementos, sangria=16, sep=15.0):
    """Lista con un punto. Cada elemento puede ser (negrita, resto)."""
    for el in elementos:
        if isinstance(el, tuple):
            cabeza, resto = el
        else:
            cabeza, resto = None, el
        h.circulo(MARGEN + 3.5, y - 3, 1.7, relleno=NEGRO)
        x = MARGEN + sangria
        if cabeza:
            h.texto(x, y, cabeza, 9.5, True, NEGRO)
            x += M.ancho(cabeza, True, 9.5) + 4
        lineas = M.envolver(resto, False, 9.5, PW - MARGEN - x)
        for i, ln in enumerate(lineas):
            h.texto(x if i == 0 else MARGEN + sangria, y, ln, 9.5, False, SUAVE)
            if i + 1 < len(lineas):
                y += 13.2
        y += sep
    return y


def numeros(h, y, elementos, sep=15.0):
    """Lista numerada."""
    for i, el in enumerate(elementos, 1):
        h.texto(MARGEN, y, "%d." % i, 9.5, True, NEGRO)
        for j, ln in enumerate(M.envolver(el, False, 9.5, ANCHO - 18)):
            h.texto(MARGEN + 18, y, ln, 9.5, False, SUAVE)
            if j + 1 < len(M.envolver(el, False, 9.5, ANCHO - 18)):
                y += 13.2
        y += sep
    return y


def tabla(h, y, filas, anchos, titulos):
    """Tabla de tres columnas con texto envuelto."""
    x0 = MARGEN
    pos = [x0]
    for w in anchos[:-1]:
        pos.append(pos[-1] + w)

    # cabecera
    h.linea(x0, y - 11, PW - MARGEN, y - 11, 1.0, NEGRO)
    for i, t in enumerate(titulos):
        h.texto(pos[i], y, t.upper(), 8, True, GRIS)
    y += 12
    h.linea(x0, y - 8, PW - MARGEN, y - 8, 0.6, CLARO)

    for fila in filas:
        alturas, envueltos = [], []
        for i, celda in enumerate(fila):
            neg = (i == 0)
            ls = M.envolver(celda, neg, 8.6, anchos[i] - 12)
            envueltos.append(ls)
            alturas.append(len(ls) * 11.4)
        alto = max(alturas)
        for i, ls in enumerate(envueltos):
            yy = y
            for ln in ls:
                h.texto(pos[i], yy, ln, 8.6, i == 0, NEGRO if i == 0 else SUAVE)
                yy += 11.4
        y += alto + 8
        h.linea(x0, y - 5, PW - MARGEN, y - 5, 0.4, CLARO)
    return y


# ─────────────────────────────────────────────────────────────────────
# Documento
# ─────────────────────────────────────────────────────────────────────

def portada(cat):
    h = hoja(cat, "Introducción")
    h.texto(MARGEN, 62, "M K", 15, True, NEGRO, esp=3.4)
    h.linea(MARGEN, 74, PW - MARGEN, 74, 1.1, NEGRO)

    y = titulo(h, 132, "Guía de cuidado", 30)
    y = titulo(h, y, "del ante y la gamuza", 30)
    y += 10
    y = parrafo(h, y, "Piel afelpada, sin sellar. Todo lo que hay que saber para "
                      "que no se aplane, no se manche y dure.", 11, GRIS, interlineado=15)
    h.linea(MARGEN, y + 12, PW - MARGEN, y + 12, 0.6, CLARO)

    y += 44
    y = rotulo(h, y, "Por qué el ante necesita otro trato")
    y = parrafo(h, y, "El ante y la gamuza son piel con el pelo levantado: no llevan "
                      "un acabado que cierre el poro. Eso les da el tacto y el color mate "
                      "que los hace distintos, y también es su punto débil. El poro abierto "
                      "absorbe agua, polvo y grasa, y el pelo se aplana con el roce.")
    y += 6
    y = parrafo(h, y, "La buena noticia es que casi todo lo que le pasa tiene arreglo, y que "
                      "con cuatro gestos se evita la mayor parte.")

    y += 30
    y = rotulo(h, y, "Las cuatro reglas")
    y = vinetas(h, y, [
        ("Cepillar antes y después.",
         "El cepillo no limpia la superficie: levanta el pelo. Es lo único que "
         "devuelve el aspecto original."),
        ("Impregnar antes de estrenar.",
         "Un protector incoloro no impermeabiliza, pero da tiempo: hace que el agua "
         "y el polvo rueden en lugar de penetrar."),
        ("Nunca mojarlo a fondo ni secarlo con calor.",
         "El calor es lo que de verdad estropea la piel: la encoge, la endurece "
         "y la agrieta."),
        ("Ante la duda, dejarlo secar del todo.",
         "Casi todos los daños vienen de frotar algo que todavía estaba húmedo."),
    ], sep=17)

    y += 22
    y = rotulo(h, y, "Nobuk o gamuza: cómo distinguirlos")
    y = parrafo(h, y, "En una foto se ven iguales y se cuidan casi igual, pero no son lo "
                      "mismo. El nobuk se lija sobre la flor de una piel de plena flor: el "
                      "pelo queda corto y fino y la piel conserva su estructura. La gamuza, "
                      "o ante, se lija sobre el lado carne de una piel dividida: el pelo es "
                      "más largo y la piel cede más.")
    y += 6
    y = parrafo(h, y, "Se distinguen en mano, con tres comprobaciones:")
    y += 10
    y = numeros(h, y, [
        "El canto. En el nobuk el lado de dentro se ve claramente más áspero y fibroso "
        "que la cara afelpada. En la gamuza las dos caras se parecen.",
        "El dedo. Pasa el dedo por encima: en el nobuk el tono apenas cambia; la gamuza "
        "\u201cescribe\u201d y se queda marcada.",
        "El estirón. Da un tirón suave: la gamuza cede bastante más.",
    ], sep=13.5)
    y += 8
    y = parrafo(h, y, "Importa para el cuidado, porque la gamuza se empapa antes y se "
                      "deforma más. Si tienes dudas, trátala como si fuera gamuza.",
                9.5, GRIS)


def rutina(cat):
    h = hoja(cat, "Rutina")
    h.texto(MARGEN, 62, "La rutina", 20, True, NEGRO)
    h.linea(MARGEN, 74, PW - MARGEN, 74, 1.1, NEGRO)

    y = 108.0
    for tit, cuando, para in [
        ("Después de cada uso", "Dos minutos", "Sacude el polvo con un cepillo de pelo "
         "suave o un paño seco, siempre en la dirección del pelo. Si el zapato se ha "
         "mojado, sécalo como se explica en la última página."),
        ("Una vez por semana", "Cepillado completo", "Cepillo de crepé o de cerda dura, "
         "enérgico y corto, siempre en la misma dirección. Es lo que levanta el pelo "
         "aplanado por el uso."),
        ("Cada cuatro o seis semanas", "Reaplicar el protector", "Con el zapato limpio y "
         "seco, a unos 20 cm, en capas finas y en un sitio ventilado. Deja secar 24 horas "
         "antes de ponértelo."),
    ]:
        y = titulo(h, y, tit, 12.5)
        h.texto(MARGEN, y, cuando, 8.5, True, GRIS)
        y += 15
        y = parrafo(h, y, para)
        y += 16

    y = rotulo(h, y, "El cepillado, en concreto")
    y = vinetas(h, y, [
        ("Dirección:", "siempre la misma, la del pelo. Si cepillas en los dos sentidos, "
         "levantas y aplastas a la vez."),
        ("Presión:", "firme pero sin clavar. No hace falta apretar para que funcione."),
        ("Cepillo:", "el de crepé, de goma, para el uso diario. El de cerda metálica solo "
         "para manchas secas y zonas muy apelmazadas, y con cuidado."),
    ], sep=15)

    y += 22
    y = rotulo(h, y, "El día que llueve")
    y = parrafo(h, y, "Es la situación más habitual y donde se cometen los dos errores "
                      "clásicos: frotar y acercarlos a la calefacción. El orden correcto:")
    y += 12
    y = numeros(h, y, [
        "Al llegar a casa, saca el exceso de agua con un paño, sin frotar, y rellena el "
        "zapato con papel de periódico.",
        "Déjalo secar a temperatura ambiente. Nunca junto a un radiador ni al sol, aunque "
        "sea lo primero que apetece hacer.",
        "Si al secarse queda un cerco, moja todo el panel por igual con una esponja "
        "húmeda y vuelve a dejarlo secar. El cerco lo produce el secado desigual, no el agua.",
        "Cuando esté seco del todo, cepilla para levantar el pelo.",
    ])


def manchas(cat):
    h = hoja(cat, "Manchas")
    h.texto(MARGEN, 62, "Manchas", 20, True, NEGRO)
    h.linea(MARGEN, 74, PW - MARGEN, 74, 1.1, NEGRO)
    y = 104.0
    y = parrafo(h, y, "Casi todo depende de una cosa: no frotar. Frotar extiende la "
                      "mancha y aplana el pelo, y a partir de ahí cuesta más arreglarlo "
                      "que la mancha original.")
    y += 16
    y = rotulo(h, y, "Antes de tocar nada")
    y = vinetas(h, y, [
        ("Prueba en una zona que no se vea:", "el interior del talón o bajo la lengüeta. "
         "Algunos productos decoloran."),
        ("Trabaja desde el borde hacia dentro:", "si empiezas por el centro, extiendes "
         "la mancha hacia la parte limpia."),
        ("Usa un paño blanco:", "los de color pueden soltar tinte sobre el ante claro."),
        ("Deja secar del todo antes de juzgar:", "en húmedo todo parece peor de lo que es."),
    ], sep=13.5)
    y += 20

    y = tabla(h, y,
        [("Agua o lluvia",
          "Sacar el exceso con un paño, rellenar con papel y dejar secar a temperatura "
          "ambiente. Queda un cerco: se quita mojando todo el panel por igual y dejándolo "
          "secar de forma uniforme.",
          "Frotar. Acercarlo a un radiador o al sol."),
         ("Barro",
          "Dejar secar del todo sin tocarlo. Cuando esté seco, cepillar.",
          "Limpiarlo húmedo: así el barro se mete en el poro."),
         ("Grasa o aceite",
          "Absorber con papel en el momento. Después cubrir con maicena o talco, dejarlo "
          "unas horas y cepillar.",
          "Usar jabón o agua: extiende la mancha."),
         ("Sal (carretera, invierno)",
          "Paño con agua y vinagre blanco a partes iguales, sin empapar. Dejar secar "
          "y cepillar.",
          "Mojarlo a fondo para aclarar."),
         ("Polvo seco",
          "Cepillado en seco, sin más.",
          "Usar productos líquidos, que lo convierten en barro."),
         ("Zonas brillantes o aplanadas",
          "Vapor de agua unos segundos sin tocar la piel, y cepillar enseguida.",
          "Planchar. Frotar en seco con fuerza."),
         ("Olor",
          "Papel de periódico dentro 24 horas, o bicarbonato en un calcetín toda la noche.",
          "Mojar el interior.")],
        anchos=[132, 244, 115],
        titulos=["Mancha", "Qué hacer", "Qué no hacer"])

    y += 10
    h.linea(MARGEN, y, PW - MARGEN, y, 0.6, CLARO)
    y += 14
    y = parrafo(h, y, "Si la mancha tiene más de un día, o es de tinta, pintura o "
                      "disolvente, llévalo a un zapatero. El ante admite casi todo "
                      "menos improvisar.", 9.5, GRIS)


def secado(cat):
    h = hoja(cat, "Secado y guardado")
    h.texto(MARGEN, 62, "Secado, guardado", 20, True, NEGRO)
    h.texto(MARGEN, 82, "y lo que nunca hay que hacer", 20, True, NEGRO)
    h.linea(MARGEN, 96, PW - MARGEN, 96, 1.1, NEGRO)

    y = 126.0
    y = rotulo(h, y, "Secarlo bien")
    y = parrafo(h, y, "Es donde más zapotos se estropean. El procedimiento, en orden:")
    y += 12
    y = numeros(h, y, [
        "Quitar los cordones y abrir el zapato todo lo que se pueda.",
        "Sacar el exceso de agua con un paño, sin frotar.",
        "Rellenar con papel de periódico o de cocina, cambiándolo cuando se empape. "
        "El papel mantiene la forma y absorbe desde dentro.",
        "Dejar a temperatura ambiente, en un sitio ventilado y a la sombra. 24 horas, "
        "a veces 48.",
        "Cuando esté seco, cepillar para levantar el pelo.",
    ])
    y += 14

    y = rotulo(h, y, "Guardarlo")
    y = vinetas(h, y, [
        ("Hormas de cedro:", "mantienen la forma y absorben la humedad. Mejor que el "
         "papel si va a estar guardado mucho tiempo."),
        ("Bolsa de tela, no de plástico:", "el plástico no deja respirar y guarda "
         "la humedad dentro."),
        ("Sitio fresco y seco, sin sol directo:", "el sol decolora el ante."),
        ("Alternar los pares:", "un zapato necesita un día entero para secarse del sudor."),
    ])
    y += 14

    y = rotulo(h, y, "Lo que nunca hay que hacer")
    y = vinetas(h, y, [
        "Lavadora, lavavajillas o remojo. La piel se deforma y se endurece, y no vuelve.",
        "Secador, radiador, calefacción o sol directo.",
        "Cepillar en húmedo: rompe las fibras.",
        "Crema o betún de piel lisa: tapa el pelo y deja una zona brillante.",
        "Lejía, amoniaco o detergente fuerte: decoloran.",
        "Frotar una mancha con fuerza: la extiende y aplana el pelo.",
    ], sep=13.5)
    y += 14

    y = rotulo(h, y, "Kit básico")
    y = parrafo(h, y, "Cepillo de crepé (goma) para el uso diario  ·  cepillo de cerda dura "
                      "para el cepillado semanal  ·  protector incoloro en espray  ·  paño "
                      "de microfibra claro  ·  papel de periódico y maicena.", 9.5, SUAVE)
    y += 20

    y = rotulo(h, y, "Cuándo llevarlo a un zapatero")
    y = parrafo(h, y, "Hay cosas que en casa salen mal. Merece la pena llevarlo si:")
    y += 10
    y = vinetas(h, y, [
        "La mancha es de tinta, pintura, disolvente o sangre.",
        "El cerco de agua no se va después de mojar el panel entero por igual.",
        "La piel se ha endurecido, ha perdido color o el pelo está pelado en una zona grande.",
        "Hay un descosido o una costura abierta.",
    ], sep=13.5)
    y += 8
    y = parrafo(h, y, "Un zapatero puede teñir, rehidratar y sustituir piezas. Lo que no "
                      "tiene vuelta atrás es la piel que se ha secado con calor.",
                9.5, GRIS)


def pie(h, pagina, total, etiqueta=""):
    """Pie propio. El del catálogo dice "MK · Catálogo", que aquí no pega."""
    w, y = h.ancho, h.pie_y
    h.linea(MARGEN, y, w - MARGEN, y, 0.6, CLARO)
    h.texto(MARGEN, y + 14, "MK · Cuidado del ante y la gamuza", 8, False, GRIS)
    if etiqueta:
        h.texto(w / 2, y + 14, etiqueta, 8, False, GRIS, izq="centro")
    h.texto(w - MARGEN, y + 14, "%d / %d" % (pagina, total), 8, False, GRIS,
            izq="derecha")


def main():
    # Catalogo.emitir escribe en la ruta del MÓDULO del catálogo, así que hay
    # que apuntarla a este documento antes de emitir. Si no, la guía se
    # guardaría encima de catalogo.pdf.
    M.SALIDA = SALIDA
    M.footer = pie          # el del catálogo no sirve aquí

    pdf = M.PDF()
    cat = M.Catalogo(pdf)
    portada(cat)
    rutina(cat)
    manchas(cat)
    secado(cat)
    n = cat.emitir("Guía de cuidado del ante y la gamuza",
                   [("Introducción", 0), ("La rutina", 1),
                    ("Manchas", 2), ("Secado y guardado", 3)])
    kb = SALIDA.stat().st_size / 1024
    print("PDF generado: %s" % SALIDA)
    print("  %d página(s) · %.0f KB" % (n, kb))


if __name__ == "__main__":
    main()
