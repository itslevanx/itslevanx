# Elementos visuales del perfil

`generate.py` crea las filas de Skills y los cierres de agradecimiento en SVG.
Las imágenes contienen sus iconos: no dependen de servicios de badges en tiempo
de visualización. Los colores y los contrastes se adaptan a los temas claro y oscuro.
Las filas se dividen en bloques de hasta tres iconos que se centran al envolver
en móvil. El cierre tiene variantes compactas para mantener el texto legible.

```sh
python scripts/profile/generate.py
```

Los nombres de los SVG incluyen una revisión basada en su contenido para evitar
que se muestre una imagen antigua. El generador actualiza las referencias del
README y elimina únicamente sus propias versiones anteriores.

Las tecnologías se editan en `GROUPS`, dentro del generador. Los iconos originales
se conservan en `scripts/profile/icons/`. La mayoría proceden de
[Devicon](https://github.com/devicons/devicon), bajo licencia MIT; los restantes
proceden de [Simple Icons](https://github.com/simple-icons/simple-icons), bajo CC0.
Las licencias se incluyen junto a los iconos. Devin se representa con un monograma
tipográfico cuando no se dispone de un símbolo en estas colecciones.
