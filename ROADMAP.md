# Roadmap

Este documento describe la hoja de ruta prevista para el proyecto *Creador de tests*. Cada versión añade capacidades específicas y se apoya en los contratos definidos en la versión anterior.

## v1 (versión inicial)

- Implementar el pipeline completo para procesar PDFs de UBUVirtual/Moodle en modo “Revisión del intento”.
- Generar un JSON canónico válido según `schema` 1.0.
- Implementar reglas de segmentación y tipado descritas en `RULES_v1.md`.
- Extracción de contenido para los tipos de pregunta listados (`single_choice`, `multi_select`, `matching`, `short_answer_text`, `numeric`, `cloze_labeled_blanks`, `cloze_table`, `multipart_short_answer`, `external_media_reference`).
- Extracción de información de corrección (`grading`), flags e incidencias.
- Generación de assets de página completa cuando sea necesario.
- Crear suite de tests con golden files (C1–C8) y pruebas unitarias por módulo.

## v1.1 (mejoras de assets y tablas)

- Incluir soporte para recortes (`page_clip`) cuando se pueda determinar de forma fiable la `bbox` de la figura o tabla de la pregunta.
- Mejorar el parseo de tablas para `cloze_table`, intentando estructurar filas y columnas en lugar de delegar a assets.
- Ajustar las reglas y el schema si aparecen nuevos tipos de pregunta tras analizar más PDFs.

## v2 (renderizado y exportación)

- Desarrollar un renderizador HTML que reproduzca lo más fielmente posible el aspecto del examen original.
- Añadir herramientas para exportar a formatos Moodle XML, GIFT o Anki, basándose en el JSON canónico.
- Incluir CLI para importar preguntas a plataformas de e‑learning.
- Explorar el uso de OCR para escaneados en versiones posteriores (si se demuestra necesario).

## Otras posibles direcciones

- Incorporar detección automática de nuevos tipos de pregunta basados en Machine Learning.
- Soporte multilingüe si se amplía a otras instancias de Moodle que usen diferentes idiomas.
