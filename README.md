# MK — catálogo + ficha interactiva

Página **autocontenida**: un solo `index.html` con el CSS y el JavaScript
embebidos. Sin dependencias, sin build y sin servidor. Las fotografías de
producto viven en `img/`.

## Organización por códigos

Cada zapatilla tiene un **código de tres dígitos** (`001`, `002`, `003`) y todo
se nombra a partir de él, de modo que una foto se puede identificar sin abrirla
y sin depender del nombre comercial del modelo.

```
zapatillas MK/                     ← carpeta de originales
├── zapatillas-001-lateral.png     ← vista principal
├── zapatillas-001-angulos.png     ← collage de vistas adicionales
├── zapatillas-002-lateral.png
└── zapatillas-003-lateral.jpeg
```

El patrón es `zapatillas-<código>-<vista>.<ext>`. Las vistas son `lateral` para
la foto principal y `angulos` para un collage de varios ángulos; si algún día
hay fotos sueltas de otras vistas, el nombre admite lo que haga falta
(`zapatillas-001-trasera.png`, `zapatillas-002-planta.png`, …).

Dentro del proyecto se repite el mismo esquema en `img/`, con la diferencia de
que las fotos van reducidas y en JPEG para que la web y el PDF no carguen
originales de 16 MB:

```
zapatillas-mk/
├── index.html                     ← web (catálogo + ficha interactiva)
├── catalogo.pdf                   ← catálogo para enviar o imprimir
├── generar-catalogo.py            ← regenera el PDF desde index.html
├── guia-cuidado-gamuza.pdf        ← guía de cuidado del ante y la gamuza
├── generar-guia.py                ← regenera la guía (reutiliza el motor)
├── verificacion-hotspots.png      ← comprobación de los puntos
└── img/
    ├── zapatillas-001-lateral.png
    ├── zapatillas-001-angulos.jpg
    ├── zapatillas-002-lateral.jpg
    └── zapatillas-003-lateral.jpg
```

El `<código>` es también el `id` del producto en los datos, así que los enlaces
profundos quedan `index.html#/zapatillas-001`.

**Al añadir un modelo**: copia la foto a `img/` como
`zapatillas-00N-lateral.jpg`, añade el objeto a `PRODUCTOS` con
`id: "zapatillas-00N"` y regenera el PDF. Si además tienes un collage con más
ángulos, guárdalo como `zapatillas-00N-angulos.jpg` y añade la clave `angulos`
al producto: el generador le creará su propia página.

## Abrir

```bash
xdg-open index.html
```

Funciona con doble clic: no hay `fetch()` ni módulos ES, así que `file://`
no da problemas de CORS.

## Las dos vistas

**1 · Catálogo** — rejilla de tarjetas al estilo de la referencia: imagen,
corazón de favoritos, insignia *Nuevo*, nombre, categoría, número de colores
y precio. A la izquierda, filtros plegables (Género, Categoría, Etiqueta) y
los conmutadores *Lo nuevo / En MK*. Arriba, buscador y ordenación.

Los filtros **funcionan de verdad**: son casillas que filtran la lista, no
decoración. El contador de resultados y el orden se recalculan al instante.

**2 · Ficha** — se entra pulsando cualquier tarjeta. Sobre la fotografía real
hay **10 puntos interactivos**: ante, lengua, cordones, puntera, cuello,
talón, logotipo, entresuela, planta y ojal. Cada uno abre su ficha de
material con descripción y tabla de especificaciones.

### Interacción en la ficha

| Acción | Cómo |
|---|---|
| Zoom | rueda del ratón (hasta 5×), o `+` / `−` |
| Desplazar | arrastrar sobre la fotografía |
| Reiniciar | botón *Reiniciar*, tecla `0` o doble clic |
| Seleccionar pieza | clic en un punto o en la lista lateral |
| Enfocar pieza | `1`–`9` (el número del punto) |
| Lupa | botón *Lupa* o tecla `L` |
| Volver al catálogo | botón *Volver* o `Esc` |

La **lupa** magnifica 2,6× sobre el zoom actual siguiendo al cursor. Está
implementada con `background-size` y `background-position` sobre la misma
imagen, así que no duplica el DOM ni pierde nitidez por reescalado de capas.

## Enlaces profundos

Cada producto tiene URL propia. `index.html#/zapatillas-001` abre su ficha
directamente; el botón *Volver* la quita. Se usa `location.hash`, sin
`pushState`, para no ensuciar el historial del navegador.

## Catálogo en PDF

`catalogo.pdf` es el catálogo listo para enviar o imprimir: **A4 apaisado**.

### Índice navegable, en vertical

La página 1 es un **índice agrupado por tipo de caña** (primero caña alta,
después caña baja), y va en **vertical** mientras que las fichas van en
apaisado. No es un capricho: en el móvil una página apaisada obliga a girar el
teléfono, y el índice es la puerta de entrada al catálogo. Un PDF admite
páginas de distinto tamaño sin problema, y el generador lleva el tamaño en
cada hoja (`Hoja.ancho` / `Hoja.alto`).

Cada modelo ocupa una fila con su miniatura, nombre, categoría, precio y la
página donde empieza, y **la fila entera es pulsable**: al tocarla, el lector
salta a la ficha de ese modelo.

Hay **dos mecanismos de navegación**, a propósito:

1. **Anotaciones `/Link`** en cada fila, con destino interno (`/Dest`), no
   URLs externas: funcionan sin conexión.
2. **Marcadores** (`/Outlines`), el panel de navegación del lector. Se abre
   con `/PageMode /UseOutlines`. Están porque algunos lectores de móvil
   ignoran las anotaciones pero sí muestran los marcadores; si los enlaces no
   responden en tu teléfono, los marcadores son el camino.

Las miniaturas reutilizan el **mismo JPEG ya incrustado** que la ficha, solo
que dibujado en pequeño: no añaden peso al archivo.

### Ficha de cada modelo

Una página por modelo, con el nombre, la categoría, el precio, una descripción
breve, la fotografía limpia y el desglose de piezas al lado.

### Composición de la ficha

- **Gancho comercial** en negrita, encima de la descripción técnica. Los
  textos viven en el diccionario `GANCHOS` del generador, indexados por el
  código del producto; si un modelo no aparece ahí, se imprime solo la
  descripción. Están en el script y no en `index.html` a propósito: el PDF
  puede tener su propio texto de venta sin tocar los datos de la web.

### Composición de la ficha

La fotografía va **a la izquierda, lo más grande que quepa** (484 × 363 pt en
A4 apaisado), y el desglose de piezas en **una sola columna a la derecha**,
con el nombre de la pieza y debajo el material y el tipo.

Antes la foto iba centrada con llamadas repartidas a los dos lados: líneas
desde cada pieza hasta su etiqueta, cinco por lado. Se descartó porque las
etiquetas ocupaban los dos márgenes y dejaban la imagen en 348 × 261 pt.
Con el desglose en una sola columna la foto casi **duplica su superficie** y
el desglose se lee igual de bien: el ancho de columna es de 240 pt y la línea
más larga de toda la colección mide 166 pt, así que nada se corta.

Las coordenadas `x`/`y` de cada pieza siguen en los datos: las usa la web para
los puntos interactivos. El PDF ya no las necesita.

### Fondo y sombra

Las fotos de estudio vienen sobre un gris con viñeta, no sobre blanco. El
generador las lleva a blanco y les añade una **sombra de contacto** para que
el zapato no parezca flotar. El proceso vive en `procesar_fondo()`:

1. Mide la luminancia y la saturación **en el propio marco** de cada foto.
   Con un umbral fijo, el `003` perdía el borde de la mediasuela, porque su
   mediasuela es casi tan blanca como su fondo.
2. Inunda desde las **cuatro esquinas**, de modo que las zonas claras
   encerradas dentro del zapato —la mediasuela crema— no se tocan aunque su
   color se parezca al del fondo.
3. Aplica una sombra difusa desplazada hacia abajo, **solo fuera de la
   silueta**: es una sombra proyectada, no un sombreado del material.

**Si el fondo ya es blanco, la foto no se toca.** Es una comprobación
deliberada (`fondo_ya_es_blanco()`): procesar una foto que ya venía sobre
blanco solo puede estropearla, y de hecho se comía la mediasuela del `001`.
Se puede desactivar todo el proceso con `BLANQUEAR_FONDO = False`.

### Página de ángulos

Un modelo puede llevar **una página extra de vistas adicionales**. Se activa
añadiendo la clave `angulos` al producto:

```js
img: "img/zapatillas-001-lateral.png",
angulos: "img/zapatillas-001-angulos.jpg",   // opcional
```

El generador coloca esa página justo detrás de la ficha del modelo, con el
collage a página completa y un pie que enumera las vistas. Como es una clave
opcional, cada zapatilla puede tener las páginas extra que necesite sin tocar
las demás: hoy solo el `001` la tiene y el catálogo sale con cuatro páginas.

No hay portada ni página aparte de especificaciones: lo que identifica al
modelo cabe en su propia hoja, y las vistas extra van con él, que es lo que
permite enviar el catálogo modelo a modelo sin perder contexto.

Para regenerarlo después de cambiar precios, textos o añadir productos:

```bash
python3 generar-catalogo.py            # escribe catalogo.pdf
python3 generar-catalogo.py otro.pdf   # o donde quieras
```

### Precio del catálogo

El precio que se imprime se fija en la constante `PRECIO_CATALOGO`, al
principio del script:

```python
PRECIO_CATALOGO = 110.0     # None para usar el precio de la web
```

Está separado a propósito: el catálogo puede llevar un precio distinto al de
la web sin tocar `index.html`. Ahora mismo el PDF muestra S/ 110.00 en los dos
modelos mientras la web conserva los suyos.

**El resto de los datos no se duplica.** El script extrae el array `PRODUCTOS`
del propio `index.html` ejecutando su sección de datos con `node`, así que
nombres, descripciones y piezas no pueden desincronizarse. Añadir un modelo a
la web lo añade al PDF sin tocar el script.

El PDF se escribe a mano, sin librerías, porque en este equipo no hay
`reportlab`, `weasyprint`, LibreOffice ni LaTeX. No es un apaño: el texto va
en Helvetica vectorial (seleccionable y buscable, comprobado con `pdftotext`)
y las fotos se incrustan como JPEG. El catálogo de cinco modelos (siete
páginas) ocupa 1453 KB.

### Coordenadas de los hotspots

En cada producto, `w` y `h` **deben describir el espacio en el que se midieron
las coordenadas `x`/`y`**, no el tamaño del archivo que se sirve. La página
coloca los puntos en porcentaje (`x / w`), de modo que el archivo puede ser
una versión reducida mientras conserve la proporción.

Es un detalle que muerde: en el segundo modelo las coordenadas se midieron
sobre el original de 3600×2688 pero se declaró `w: 2800`, y los puntos
salieron desplazados en la web y en el PDF. Si al añadir una foto los puntos
no caen donde deberían, casi siempre es esto.

> Esto es un catálogo diseñado a partir de los datos, no una captura de la
> web. Los dos comparten contenido, pero la maquetación es independiente:
> la web es interactiva y el PDF es para leer e imprimir.

## Añadir un producto

1. Copia la fotografía a `img/` con un nombre sin espacios ni acentos.
2. Añade un objeto al array `PRODUCTOS` en `index.html`.

```js
{
  id: "zapatillas-004",              // se usa en el enlace profundo
  nombre: "MK Algo Low",
  categoria: "Zapatillas para mujer",
  genero: "Mujer", tipo: "Caña baja",
  precio: 349.90,
  colores: 1,
  nuevo: true,
  etiquetas: ["Nuevo"],
  img: "img/otro-modelo.png",
  w: 3600, h: 2688,                  // espacio de coordenadas de los hotspots
  descripcion: "Una o dos frases sobre el calzado. Salen en el PDF.",
  piezas: [ /* ... */ ]
}
```

`w` y `h` deben describir **el espacio en el que se midieron las coordenadas
`x`/`y`**, no necesariamente el tamaño del archivo servido: los puntos se
colocan en porcentaje, así que el archivo puede ser una copia reducida
mientras conserve la proporción. Si declaras un tamaño distinto al de la
medición, los hotspots se desplazan.

### Colocar los hotspots de una imagen nueva

Las coordenadas `x`/`y` de cada pieza están en píxeles de la imagen original.
Para sacarlas, superpón una rejilla sobre la foto:

```bash
magick foto.png -stroke 'rgba(255,0,0,.45)' -strokewidth 1 -fill none \
  -draw "line 0,0 0,1086 line 0,0 1448,0 ..." rejilla.png
```

O mide directamente en cualquier editor. Después comprueba el resultado
dibujando los puntos candidatos antes de tocar el HTML — así se detecta un
punto que cae fuera de la pieza antes de que llegue a la página.

## Estructura del archivo

Secciones numeradas dentro de `index.html`:

1. **Datos** — `PRODUCTOS` (imagen, tamaño y piezas) y `FILTROS`.
2. **Estado** — el objeto `E` del catálogo.
3. **Catálogo** — filtrado, orden y pintado de tarjetas.
4. **Detalle** — lienzo, zoom, paneo, lupa y fichas de material.
5. **Eventos** — delegación, puntero, rueda y teclado.
6. **Arranque**.

## Decisiones

**Fondo blanco.** La página y las tarjetas son blancas. Como las fotografías
de producto ya vienen sobre blanco, la zapatilla «flota» sin recuadro, que es
más limpio que el gris de las fichas de producto habituales.

**Puntos monocromos.** Los hotspots son blancos con borde negro en lugar de
llevar color. Sobre una zapatilla negra el punto blanco destaca, y sobre el
fondo blanco el borde lo mantiene visible. Un punto de color competiría con
el producto, que es lo que el usuario ha venido a mirar.

**Límite de zoom.** El zoom llega a 5×, pero la nitidez real está limitada por
la resolución del archivo de origen. El segundo modelo, a 3600 px, aguanta el
zoom bastante mejor que el primero, a 1448 px. Mejorar el primero es sustituir
el archivo por una foto mayor y actualizar `w` y `h`.

## Verificación realizada

- `node --check` sobre el JavaScript embebido: sin errores.
- Los `id` que usa el JavaScript existen en el HTML.
- Las 30 piezas (10 por modelo) tienen coordenadas dentro de los límites de su
  imagen, y se comprobó **visualmente** que cada punto cae sobre la pieza
  correcta. `verificacion-hotspots.png` es esa comprobación: los tres modelos
  con sus 30 puntos dibujados sobre la fotografía.
- Todas las texturas de muestra (`tx-*`) referenciadas en los datos tienen su
  regla CSS, y las dos imágenes referenciadas existen en `img/`.
- **El PDF se verificó visualmente**: se rasterizaron sus páginas con
  `pdftoppm` y se revisó cada una. Se confirmó con `pdftotext` que el texto es
  vectorial y extraíble, con `pdffonts` que usa Helvetica con codificación
  WinAnsi, y con `pdfimages` que **cada página lleva su propia fotografía**.
- La ausencia de círculos se comprobó leyendo los flujos de contenido del PDF:
  **cero curvas bezier**, que es como se dibujan. No basta con quitarlos del
  código si algo los reintroduce.
- Dos ejecuciones seguidas producen un PDF idéntico y no quedan temporales.

Dos fallos que aparecieron en esta revisión y quedaron corregidos, por si
vuelven a darse al añadir modelos:

1. **Marcadores que no aparecían.** En el objeto `/Outlines`, `/First` y
   `/Last` son **referencias indirectas**: hay que escribirlas como `29 0 R`,
   no como `29`. Sin el `0 R` el PDF se genera igual y no da error, pero el
   panel de marcadores queda vacío. Se detectó recorriendo el árbol de
   marcadores del archivo generado y comprobando que las seis entradas
   resuelven a su página.
2. **Puntos desplazados.** Las coordenadas del segundo modelo se midieron
   sobre el original de 3600×2688, pero se declaró `w: 2800` (el JPEG
   reducido). Los 10 puntos salieron corridos en la web y en el PDF.
3. **Foto repetida.** El generador usaba un único archivo temporal para todos
   los productos, y la caché de imágenes es por ruta, así que la segunda
   página salió con la fotografía de la primera. Ahora hay un temporal por
   producto.

> Limitación honesta: la **página web** no se pudo rasterizar en un navegador
> headless (Brave se cuelga al arrancar sin pantalla, y no hay Chromium,
> Firefox, Playwright ni WeasyPrint). Su HTML y su CSS se validaron
> estáticamente, y los hotspots sobre las fotografías sí se comprobaron
> visualmente, pero **la maquetación de la web conviene mirarla en el
> navegador**. El PDF, en cambio, está revisado página a página.

### El corte del blanco, medido

`fondo_ya_es_blanco()` decide si una foto se procesa o se deja tal cual, y el
umbral está medido, no elegido a ojo. En esta colección las medianas del marco
son:

| Modelo | Mediana del fondo | Qué se hace |
|---|---|---|
| 001 | 254 | Ya es blanco: **no se toca** |
| 002 | 223 | Se blanquea |
| 003 | 215 | Se blanquea |
| 004 | 246 | Se blanquea |
| 005 | 246 | Se blanquea |

El corte está en 250, entre el 246 del 004 y el 254 del 001. Procesar una foto
que ya venía sobre blanco (el 001) le comía la mediasuela, porque su mediasuela
clara se confunde con el fondo; por eso la comprobación existe.
