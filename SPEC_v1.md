# Especificación v1

Este documento define la especificación funcional y contractual de la **versión 1** del proyecto *Creador de tests*.

## Objetivo

Procesar PDFs en formato “Revisión del intento” de UBUVirtual/Moodle y generar un **JSON canónico** que refleje de manera estructurada las preguntas, tipos de respuesta, puntuaciones y cualquier información relevante, de forma determinista y validable. La salida sirve como base para futuros renderizadores (por ejemplo, HTML idéntico al original) y para análisis y corrección automática.

## Alcance

### Tipo de documentos soportados

- PDFs **digitales** (no escaneados) procedentes de UBUVirtual/Moodle en modo “Revisión del intento”.
- Cada bloque se introduce con un encabezado `Pregunta N` (puede haber variaciones en su alineación o ausencia, para lo cual se emplean marcadores secundarios).

### Unidades de procesamiento

1. **Extracción y normalización**: se obtienen las líneas de texto de cada página con su layout; se eliminan encabezados/pies repetidos y se normaliza la codificación.
2. **Segmentación**: se agrupan líneas en bloques de pregunta, usando `Pregunta N` y marcadores secundarios (`Seleccione una`, `Respuesta:`, etc.).
3. **Tipado**: se determina el tipo de pregunta (`kind`) mediante reglas de detección prioritarias (ver `RULES_v1.md`).
4. **Extracción específica**: según el tipo identificado, se extraen opciones, respuestas, pares de emparejamiento, valores numéricos, etiquetas de blancos, etc., rellenando la estructura `content` definida en `DATA_MODEL.md`.
5. **Grading**: se captura el estado de corrección (`Correcta`, `Parcialmente correcta`, `Incorrecta`), la puntuación obtenida y máxima, texto de penalización y feedback cuando están disponibles.
6. **Flags e incidencias**: se marcan flags (`asset_required`, `math_or_symbols_risky`, `requires_external_media`) y se registran incidencias (`issues[]`) cuando sea necesario para informar de pérdidas de información, tablas no estructurables, etc.
7. **Generación de assets**: en v1, si `asset_required=true`, se generan capturas **full page** de las páginas involucradas y se registran en `stem.assets[]` para preservar contenido visual.
8. **Validación**: el JSON generado debe validar contra `schemas/exam_doc-1.0.schema.json`.

## Entrada

- Ruta a uno o varios archivos PDF.
- Parámetros opcionales (para el CLI futuro): directorio de salida, directorio para assets.

## Salida

- Un archivo JSON conforme al schema `exam_doc-1.0`.
- Cuando se requiere, un directorio con assets renderizados.

## Criterios de aceptación (v1)

1. **Correctitud estructural**: el JSON generado valida sin errores contra el schema.
2. **Segmentación**: el número de preguntas y su numeración (`number`) coincide con lo observado en el PDF.
3. **Tipado**: cada pregunta recibe el `kind` adecuado conforme a las reglas de detección.
4. **Extracción de contenido**: campos `content` (opciones, pares, blanks, etc.) se llenan correctamente en las preguntas representativas de cada tipo.
5. **Grading**: se capturan correctamente estado (`status`), puntuación obtenida, puntuación máxima, penalización y feedback.
6. **Flags y assets**: en preguntas donde la extracción textual no basta (fórmulas, tablas de verdad, árboles), se activa `asset_required` y se generan los assets de página completa.
7. **Incidencias**: se reportan incidencias con códigos predefinidos cuando corresponda (ver `RULES_v1.md`).
8. **Determinismo**: con la misma entrada se obtienen los mismos datos (salvo rutas de ficheros de assets).

## Requisitos no funcionales

- No se utilizará OCR en v1; únicamente extracción de texto digital y renderizado de páginas.
- El sistema debe ser modular para permitir la incorporación de nuevos tipos y políticas de assets en versiones futuras.
- Los fallos de extracción no deben provocar pérdida de información: en caso de no poder estructurar una pregunta, se conservará el `raw.block_text` y se emitirá una incidencia.

## Fuera de alcance (v1)

- Exportación a formatos Moodle XML o GIFT.
- Renderizado de un HTML idéntico al examen original.
- Soporte para PDFs escaneados u OCR.
