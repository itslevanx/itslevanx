# Banner del perfil

El banner convierte las tres imágenes originales en dibujos de puntos y anima
las transiciones dentro de un SVG autónomo, sin JavaScript ni servicios externos.
La secuencia es **Leonardo → Luffy Gear 5 → robot leyendo → Leonardo**.
Cada figura permanece 3,6 segundos y cada transición dura 1,4 segundos.

## Regenerar

Desde la raíz del repositorio, con Python 3.10 o posterior:

```sh
python -m pip install -r scripts/banner/requirements.txt
python scripts/banner/generate.py
```

Se generan `assets/profile-banner-dark.svg` y `assets/profile-banner-light.svg`.
El README elige la variante con `<picture>` y `prefers-color-scheme`.
Con `prefers-reduced-motion: reduce` se muestra solamente el retrato estático.

## Personalizar

- Datos, tecnologías y orden de imágenes: `scripts/banner/profile.json`.
- Imágenes originales: `assets/source/portrait.png`, `luffy.png` y `robot.png`.
- Colores y tiempos: `THEMES`, `HOLD` y `TRANSITION` en `generate.py`.
- La máscara y el recorte del retrato están ajustados a la foto suministrada;
  hay que revisarlos si se cambia esa foto. Luffy y el robot conservan su transparencia.

Las tecnologías del panel proceden del README existente. La sección `goal`
expresa la orientación hacia ML Engineer, y no un cargo profesional actual.
El banner no incluye un bloque de contacto.

La composición de terminal y el tratamiento del retrato en puntos toman como
referencia [AlexanderJSO/AlexanderJSO](https://github.com/AlexanderJSO/AlexanderJSO).
Las imágenes fueron suministradas por el propietario del perfil. Luffy pertenece
a One Piece y se utiliza como referencia personal de afición al anime.
