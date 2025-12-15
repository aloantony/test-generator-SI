# Plan de pruebas (v1)

Este documento describe los criterios de prueba para validar la implementación de la versión 1 del *Creador de tests*. El objetivo de las pruebas es garantizar que el JSON generado cumpla con el contrato especificado y que se detecten adecuadamente los distintos tipos de preguntas y situaciones de error.

## 1. Golden tests

Se utilizarán ficheros “golden” como referencia de salida correcta. Para cada PDF de entrada (C1–C8) se creará:

1. Un fichero `golden/Cx.json` que contiene el JSON canónico esperado para ese PDF completo.
2. Ficheros individuales por pregunta ancla en `golden/questions/Cx_Qn.json` que contienen la salida esperada de preguntas representativas (por ejemplo, aquellas con fórmulas o puntuaciones parciales).

### 1.1. Validación de schema

- Cada `golden/<PDF>.json` debe validar correctamente contra `schemas/exam_doc-1.0.schema.json`.
- Las pruebas de schema comprobarán la presencia de campos obligatorios y la ausencia de campos no permitidos.

### 1.2. Segmentación

- Se comprobará que el número de preguntas (`len(questions)`) coincide con la cifra esperada de cada PDF.
- Se verificará que cada `question.number` corresponda al número visible en el PDF.

### 1.3. Tipado

- Para las preguntas ancla se validará que `kind` coincida con el tipo esperado (single/multi/matching/numeric/cloze, etc.).
- Se debe respetar el orden de prioridades descrito en `RULES_v1.md`.

### 1.4. Extracción

- Se compararán campos específicos del `content` para las preguntas ancla:
  - opciones y su texto para preguntas `single_choice` y `multi_select`.
  - pares para preguntas de emparejamiento.
  - etiquetas y valores para blanks etiquetados (`cloze_labeled_blanks`).
  - valores numéricos y parámetros de formato (`numeric_format`).
- Para `cloze_table` se verificará que `table` esté a `null` si no se ha podido estructurar, y que se haya activado `asset_required`.

### 1.5. Grading y penalizaciones

- Se comprobará que `grading.status` refleje el valor correcto (“Correcta”, “Parcialmente correcta” o “Incorrecta”).
- Se validarán `score_awarded` y `score_max`, permitiendo valores negativos en penalizaciones.
- Se revisará que `penalty_rule_text` no sea nulo cuando el enunciado mencione penalizaciones.

### 1.6. Flags y assets

- Se verificará que `flags.asset_required=true` en preguntas con pérdida de fórmulas u objetos gráficos (por ejemplo, lógica y árboles de juego).
- Se comprobará que `flags.requires_external_media=true` para preguntas que refieren a vídeos.
- Se testeará que al activarse `asset_required` aparezca al menos un asset con `type="full_page"` en `stem.assets`.

### 1.7. Incidencias

- Para cada golden se verificará que se registran las incidencias esperadas (`issues[]`), como `OPTIONS_MISSING_TEXT` y `MATH_TEXT_LOSS` en preguntas de lógica.


## 2. Pruebas unitarias

Además de los golden tests, habrá pruebas unitarias por módulo:

### 2.1. Validación de schema

- Prueba `test_schema_validation.py` que tome cada fichero JSON generado y llame al validador JSON Schema.

### 2.2. Segmentación

- Prueba `test_segmentation.py` para asegurar que se detectan correctamente los bloques de pregunta en un PDF con multiples tipos.

### 2.3. Tipado

- Prueba `test_typing.py` para comprobar que el `kind` se asigna correctamente en casos frontera (p.ej., mezcla de marcadores “Seleccione…” y “Asocia…”).

### 2.4. Extracción por tipo

- Un test por extractor (`test_extraction_choice.py`, `test_extraction_matching.py`, etc.) que verifique la correcta extracción de opciones, pares, numéricos, blanks, etc.

### 2.5. Flags y assets

- Prueba `test_flags_assets.py` que evalúe la activación de `asset_required`, `math_or_symbols_risky` y `requires_external_media` y la creación de assets.

## 3. Criterios de éxito

Las pruebas se considerarán superadas cuando:

- Todos los ficheros JSON generados validen contra el schema.
- El número de preguntas y sus `kind` coincidan con los golden.
- Los campos de `content`, `grading`, `flags` y `issues` coincidan con los esperados en los golden o satisfagan las condiciones del test unitario.
- No se produzcan errores inesperados durante la ejecución de las pruebas.
