# Publicar la tienda en GitHub Pages

## Qué se publica

Solo la carpeta `docs/`: la web (`index.html`) y las fotos (`img/`), 3,7 MB en
total. Los PDF, los scripts, la hoja de revisión de materiales y la imagen de
verificación **se quedan fuera**, porque no tienen nada que hacer en un sitio
público.

Se publica desde `docs/` en vez de la raíz para no arrastrar el resto del
proyecto. GitHub Pages sabe servir desde ahí.

## 1 · Generar `docs/`

```bash
python3 publicar.py
```

Hay que repetirlo cada vez que cambies `index.html` o las fotos.

## 2 · Subirlo a GitHub

Crea un repositorio **vacío** en GitHub (sin README ni licencia), por ejemplo
`zapatillas-mk`. Después, desde esta carpeta:

```bash
git remote add origin https://github.com/TU_USUARIO/zapatillas-mk.git
git push -u origin main
```

## 3 · Activar Pages

En el repositorio: **Settings → Pages**

- **Source**: `Deploy from a branch`
- **Branch**: `main` y carpeta **`/docs`**
- **Save**

En un minuto está en:

```
https://TU_USUARIO.github.io/zapatillas-mk/
```

## 4 · Cuando cambies algo

```bash
python3 publicar.py
git add -A
git commit -m "Actualizo el catálogo"
git push
```

GitHub vuelve a publicar solo, en menos de un minuto.

## Por qué funciona sin tocar nada

- La página **no tiene rutas absolutas**: todas las referencias son relativas,
  así que funciona igual en `https://usuario.github.io/repo/` que abierta
  desde el disco.
- **No usa `fetch`, ni módulos ES, ni `localStorage`, ni `history.pushState`.**
  Nada que necesite un servidor.
- Los enlaces a cada modelo van por el **hash** de la URL
  (`#/zapatillas-001`), no por rutas. Eso evita el problema típico de las
  aplicaciones de una sola página en Pages, que necesitan reescribir rutas y
  Pages no lo hace.

## Lo que GitHub Pages NO puede hacer

Pages solo sirve archivos estáticos. Puede mostrar el catálogo y llevar a
quien lo mire a donde quieras, pero **no procesa pagos, no lleva carrito y no
controla stock**. Para vender de verdad hay tres caminos que sí funcionan
sobre Pages:

1. **Pedido por WhatsApp** — un botón por modelo que abre WhatsApp con el
   mensaje ya escrito. Es lo más habitual y no cuesta nada.
2. **Enlace de pago** — un botón que abre un link de Mercado Pago o Stripe
   creado de antemano. El cobro lo gestiona la pasarela, no la web.
3. **Tienda completa** — con carrito, tallas y envíos ya hace falta una
   plataforma: Shopify, Tiendanube o WooCommerce. Pages no llega.

En los dos primeros casos el sitio sigue siendo estático y sigue funcionando
en Pages sin problema.
