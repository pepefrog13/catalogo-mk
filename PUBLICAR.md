# Publicar la tienda en GitHub Pages

El sitio ya está preparado en `docs/`: la web, las 13 fotos y un archivo
`.nojekyll`. Son 6,4 MB, y el repositorio local ya tiene los commits hechos en
la rama `main`.

Falta subirlo. **Ahí está el obstáculo real**: esta máquina no tiene ninguna
clave SSH ni token guardado, así que GitHub todavía no sabe quién eres. Hay
tres caminos; el primero es el más rápido.

---

## Camino A · Token (recomendado para empezar)

### 1 · Crear el repositorio

En https://github.com/new

- **Name**: `catalogo-mk`
- **Public** ← importante: Pages gratis solo funciona en repositorios públicos
- **No** marques "Add a README", ni licencia, ni .gitignore. Tiene que nacer vacío.

Quedará en `https://github.com/Jchino24/catalogo-mk`

### 2 · Crear un token de acceso

En https://github.com/settings/tokens

- **Generate new token (classic)**
- **Note**: `publicar catalogo`
- **Expiration**: 90 días va bien
- **Scopes**: marca solo **`repo`**
- Pulsa **Generate token** y **cópialo**

> El token es una contraseña. No lo pegues en ningún chat ni lo dejes dentro
> del proyecto. Si se pierde, se revoca en esa misma página y se crea otro.

### 3 · Subirlo

```bash
cd /home/josfx/Documentos/deepseek-harness/default-workspace/zapatillas-mk
git remote add origin https://github.com/Jchino24/catalogo-mk.git
git push -u origin main
```

Te pedirá:

- **Username**: `Jchino24`
- **Password**: el **token**, no tu contraseña de GitHub

### 4 · Activar Pages

En el repositorio: **Settings → Pages**

- **Source**: `Deploy from a branch`
- **Branch**: `main` y carpeta **`/docs`**
- **Save**

En un minuto está en:

```
https://jchino24.github.io/catalogo-mk/
```

---

## Camino B · Clave SSH (no caduca)

Se genera un par de claves, se le da la pública a GitHub y no vuelves a
escribir credenciales.

```bash
ssh-keygen -t ed25519 -C "jchino@ulasalle.edu.pe" -f ~/.ssh/id_ed25519 -N ""
cat ~/.ssh/id_ed25519.pub
```

Copia esa salida y pégala en https://github.com/settings/keys → **New SSH key**.

Después:

```bash
cd /home/josfx/Documentos/deepseek-harness/default-workspace/zapatillas-mk
git remote add origin git@github.com:Jchino24/catalogo-mk.git
git push -u origin main
```

---

## Camino C · Sin git ni GitHub: Netlify Drop

Si no quieres pelearte con tokens ni claves:

1. Entra en https://app.netlify.com/drop
2. Arrastra **la carpeta `docs/`** entera a la ventana
3. Te da una URL pública al momento

También es gratis y permanente. La diferencia es que no queda versionado: cada
vez que cambies algo hay que volver a arrastrar la carpeta.

---

## Qué se publica

Solo lo que hay en `docs/`: `index.html` y las fotos.

Se quedan fuera los PDF, los scripts, la hoja de revisión de materiales y la
imagen de verificación de los puntos, que no tienen nada que hacer en un sitio
público. Por eso se publica desde `docs/` y no desde la raíz.

## Cuando cambies algo

```bash
cd /home/josfx/Documentos/deepseek-harness/default-workspace/zapatillas-mk
python3 preparar-imagenes.py    # solo si has cambiado fotos
python3 publicar.py             # regenera docs/
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
- Los enlaces a cada modelo van por el **hash** de la URL (`#/zapatillas-001`),
  no por rutas. Eso evita el problema típico de las aplicaciones de una sola
  página en Pages, que necesitan reescribir rutas y Pages no lo hace.
- `.nojekyll` desactiva Jekyll, que si no ignora los archivos que empiezan por
  guion bajo y puede reescribir cosas sin avisar.

## Lo que GitHub Pages no puede hacer

Pages solo sirve archivos estáticos. Muestra el catálogo y lleva a quien lo
mire a donde quieras, pero **no procesa pagos, no lleva carrito y no controla
stock**. Para vender de verdad hay tres caminos que sí funcionan sobre Pages:

1. **Pedido por WhatsApp** — un botón por modelo que abre WhatsApp con el
   mensaje ya escrito. Es lo más habitual y no cuesta nada.
2. **Enlace de pago** — un botón que abre un link de Mercado Pago o Stripe
   creado de antemano. El cobro lo gestiona la pasarela.
3. **Tienda completa** — con carrito, tallas y envíos hace falta una
   plataforma: Shopify, Tiendanube o WooCommerce.
