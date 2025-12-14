# Política de assets (v1)

Este documento define la política para la generación de assets en la versión 1 del proyecto. Los assets son recortes de página o páginas completas renderizadas como imágenes que se añaden al campo `stem.assets[]` de las preguntas para preservar contenido visual que pueda perderse al extraer el texto.

## 1. Cuándo generar assets

Se genera un asset cuando `flags.asset_required=true`. Este flag se activa en casos como:

- El enunciado o las opciones hacen referencia a una **figura**, **tabla de verdad**, **árbol de juego**, **grafo** u otro elemento visual imprescindible.
- El contenido extraído del PDF presenta **símbolos lógicos/matemáticos** complejos (¬, ∧, →, ∀, etc.) que puedan perderse o distorsionarse.
- Se detecta que las opciones enumeradas (`a./b./c./d.`) carecen de texto significativo, lo que sugiere que las fórmulas o expresiones se han perdido en la extracción.

## 2. Tipo de asset en v1

En la versión 1 la política es conservadora: se captura **la página completa** donde aparece la pregunta.

### Estructura del objeto `Asset`

```json
{
  "type": "full_page",
  "page": <número de página 0‑based>,
  "bbox": null,
  "file": "assets_out/<pdf_base_name>/Q{number}_p{page}.png"
}
```

En futuras versiones (v1.1 o v2) se podrá incluir un recorte de página (`page_clip`) cuando se obtenga con fiabilidad la `bbox` del elemento relevante.

## 3. Ubicación y nomenclatura

- Los assets se guardan en el directorio `assets_out/<pdf_base_name>/`.
- La nomenclatura propuesta es `Q{number}_p{page}.png`, donde:
  - `{number}` es el número de pregunta.
  - `{page}` es el índice de la página donde se recorta.

Ejemplo: para el PDF `C8…pdf`, la pregunta 7 en la página 3 generaría el asset `assets_out/C8/Q7_p3.png`.

## 4. Almacenamiento y versionado

- El directorio `assets_out/` no debería versionarse en el control de código fuente; se incluye un archivo `.gitkeep` para preservar la carpeta vacía.
- Las rutas relativas a los assets se almacenan en el JSON, permitiendo así regenerar el proyecto en distintas máquinas sin conflictos de ruta absoluta.
