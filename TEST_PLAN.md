# Plan de pruebas (v1)

Este documento describe los criterios de prueba para validar la implementación de la versión 1 del *Creador de tests*. El objetivo de las pruebas es garantizar que el JSON generado cumpla con el contrato especificado y que se detecten adecuadamente los distintos tipos de preguntas y situaciones de error.

## 1. Golden tests

Se utilizarán ficheros "golden" como referencia de salida correcta. Para cada PDF de entrada (C1–C8) se generan:

1. Un fichero `outputs/Cx.json` que contiene el JSON canónico para ese PDF completo.
2. Estos ficheros golden se generan usando la CLI: `creador-tests parse --in fixtures/Cx*.pdf --out outputs/Cx.json --assets-out assets_out/Cx`

Los golden files se almacenan en `outputs/` y sirven como referencia para validar:
- Validación de schema
- Determinismo (mismo input = mismo output)
- Conteos mínimos por tipo de pregunta
- Integridad estructural

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

## 3. Invariantes comprobadas

Las pruebas verifican las siguientes invariantes críticas:

### 3.1. Validación de schema
- **Invariante**: Todos los JSON generados deben cumplir estrictamente con `schemas/exam_doc-1.0.schema.json`.
- **Comprobación**: Cada golden file (C1-C8) se valida contra el schema usando `jsonschema`.
- **Tests**: `test_golden_schema_validation` en `test_golden_complete.py`.

### 3.2. Determinismo
- **Invariante**: El mismo PDF de entrada debe producir exactamente el mismo JSON (salvo rutas de assets temporales).
- **Comprobación**: Se parsea el mismo PDF dos veces y se comparan los resultados normalizados (excluyendo rutas de archivos de assets).
- **Tests**: `test_golden_determinism` en `test_golden_complete.py`.
- **Importancia**: Garantiza reproducibilidad y que cambios en el código se reflejen de forma predecible.

### 3.3. Conteos mínimos por tipo
- **Invariante**: Cada PDF debe tener al menos un número mínimo de preguntas de cada tipo detectado.
- **Comprobación**: Se cuenta el número de preguntas por `kind` y se verifica que cumpla con los mínimos esperados.
- **Tests**: `test_golden_type_counts` en `test_golden_complete.py`.
- **Conteos esperados** (mínimos):
  - **C1**: matching ≥ 5, short_answer_text ≥ 7
  - **C2**: matching ≥ 1, single_choice ≥ 2, multi_select ≥ 2, numeric ≥ 1, short_answer_text ≥ 2
  - **C3**: multipart_short_answer ≥ 1
  - **C4**: multipart_short_answer ≥ 1
  - **C5**: single_choice ≥ 4, multi_select ≥ 2, matching ≥ 1, cloze_table ≥ 1, multipart_short_answer ≥ 1, short_answer_text ≥ 3
  - **C6**: matching ≥ 3, multi_select ≥ 1, numeric ≥ 1, short_answer_text ≥ 7 (multipart_short_answer convertido a short_answer_text si tiene < 2 items)
  - **C7**: cloze_labeled_blanks ≥ 2, numeric ≥ 2, short_answer_text ≥ 2
  - **C8**: matching ≥ 5, single_choice ≥ 4, multi_select ≥ 1, short_answer_text ≥ 6 (multi_select convertido a short_answer_text si tiene < 2 options)

### 3.4. Integridad estructural
- **Invariante**: Todos los campos obligatorios deben estar presentes y tener el tipo correcto.
- **Comprobación**: Se verifica la presencia de `schema_version`, `source`, `questions`, `issues` y todos los subcampos requeridos.
- **Tests**: `test_golden_structure_integrity` en `test_golden_complete.py`.
- **Campos verificados**:
  - Top-level: `schema_version="1.0"`, `source`, `questions[]`, `issues[]`
  - Source: `file_name`, `doc_type="moodle_attempt_review"`, `page_count > 0`
  - Question: `id`, `number`, `kind`, `stem`, `grading` (nullable), `content`, `raw`, `flags`, `issues[]`
  - Raw: `block_text`, `pages[]` (non-empty)
  - Flags: `asset_required`, `math_or_symbols_risky`, `requires_external_media`
  - Asset requirement: Si `asset_required=true`, debe haber al menos un asset en `stem.assets[]`

### 3.5. Ausencia de tipos inválidos
- **Invariante**: No se permite `kind="unknown"` (el schema no lo acepta).
- **Comprobación**: Se verifica que ningún `question.kind` sea `"unknown"`.
- **Tests**: `test_golden_type_counts` verifica esta condición.
- **Nota**: Cuando no se puede detectar el tipo, se usa `short_answer_text` como fallback y se añade un issue.

### 3.6. Cumplimiento de restricciones del schema
- **Invariante**: Las preguntas deben cumplir todas las restricciones del schema (minItems, maxItems, etc.).
- **Comprobación**: 
  - `single_choice.correct` tiene máximo 1 elemento (maxItems: 1)
  - `multi_select.options` tiene mínimo 2 elementos (minItems: 2)
  - `multipart_short_answer.items` tiene mínimo 2 elementos (minItems: 2)
  - `multipart_short_answer.items[].index` es ≥ 1 (minimum: 1)
- **Tests**: `test_golden_schema_validation` detecta violaciones.
- **Nota**: El CLI aplica correcciones automáticas cuando detecta violaciones (convierte tipos o trunca arrays) y añade issues para documentar los cambios.

## 4. Criterios de éxito

Las pruebas se considerarán superadas cuando:

- Todos los ficheros JSON generados validen contra el schema.
- El número de preguntas y sus `kind` coincidan con los golden.
- Los campos de `content`, `grading`, `flags` y `issues` coincidan con los esperados en los golden o satisfagan las condiciones del test unitario.
- No se produzcan errores inesperados durante la ejecución de las pruebas.
- **Todas las invariantes documentadas se cumplan** (determinismo, conteos mínimos, integridad estructural).
