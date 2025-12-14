# Modelo de datos (v1)

Este documento describe la estructura del **JSON canónico** generado por la versión 1 del proyecto *Creador de tests*, así como la semántica de cada campo. La implementación debe seguir fielmente este contrato y validar la salida contra el `schema` oficial ubicado en `schemas/exam_doc-1.0.schema.json`.

## 1. Raíz del documento (`ExamDoc`)

```json
{
  "schema_version": "1.0",
  "source": { … },
  "questions": [ … ],
  "issues": [ … ]
}
```

- **`schema_version`**: cadena fija "1.0" que indica la versión del schema.
- **`source`**: objeto con información sobre la entrada (nombre de fichero, tipo de documento, número de páginas).
- **`questions`**: array de objetos `Question` que representan cada unidad de pregunta detectada.
- **`issues`**: array de incidencias a nivel de documento (no asociado a una pregunta concreta).

## 2. Objeto `source`

Campos obligatorios:

| Campo       | Tipo     | Descripción                                   |
|-------------|----------|-----------------------------------------------|
| `file_name` | string   | Nombre del PDF de entrada.                    |
| `doc_type`  | string   | Tipo de documento, en v1 siempre `moodle_attempt_review`. |
| `page_count`| integer  | Número total de páginas del PDF.              |


## 3. Estructura de `Question`

Cada elemento del array `questions` debe cumplir con uno de los subtipos definidos a continuación. Todos comparten una base común (`QuestionBase`) con los siguientes campos:

- **`id`** (string): identificador único de la pregunta dentro del documento (por ejemplo `Q7`).
- **`number`** (integer): número de pregunta según el PDF.
- **`kind`** (string): tipo de pregunta. Debe coincidir con uno de los valores listados en la sección 4.
- **`stem`** (object): enunciado de la pregunta con posible lista de assets.
- **`grading`** (object o null): información de corrección. Siempre presente (nullable).
- **`content`** (object): estructura específica según el tipo de pregunta.
- **`raw`** (object): texto original y páginas de procedencia.
- **`flags`** (object): indicadores transversales.
- **`issues`** (array): incidencias asociadas a la pregunta.

### 3.1. Campo `stem`

Objeto con:
- **`text`**: cadena con el texto del enunciado. Puede contener huecos o estar mutilado si el PDF tiene fórmulas que no se extraen correctamente.
- **`assets`**: array de objetos `Asset`. En v1, si `flags.asset_required=true` se añadirá al menos un asset con `type="full_page"`.

### 3.2. Campo `grading`

Estructura opcional (puede ser null) que captura la información de corrección:

- **`status`**: `"Correcta"`, `"Parcialmente correcta"`, `"Incorrecta"` o null.
- **`score_awarded`**: número con la nota obtenida (puede ser negativo).
- **`score_max`**: número con la nota máxima de la pregunta.
- **`penalty_rule_text`**: cadena con el texto de penalización si aparece (“las respuestas incorrectas restan…”).
- **`feedback`**: texto de retroalimentación (“¡Correcto! …”), o null.

### 3.3. Campo `raw`

- **`block_text`**: texto completo del bloque extraído para la pregunta (sin procesar), permite inspeccionar el original cuando hay problemas de parsing.
- **`pages`**: array de índices de página (0‑based) donde aparece la pregunta.

### 3.4. Campo `flags`

Objeto con indicadores booleanos:

| Flag                         | Significado                                                                                     |
|-----------------------------|--------------------------------------------------------------------------------------------------|
| `asset_required`            | `true` si la pregunta depende de contenido visual o el texto extraído no es fiable.              |
| `math_or_symbols_risky`     | `true` si se detectan símbolos lógicos o matemáticos que puedan perderse en el texto extraído.   |
| `requires_external_media`   | `true` si la pregunta hace referencia a un vídeo u otro recurso no embebido en el PDF.           |

### 3.5. Campo `issues`

Array de incidencias asociadas a la pregunta. Cada incidencia tiene: `level` (info/warn/error), `code` (ver `RULES_v1.md`), `where` (identificador) y `msg` (mensaje descriptivo).

## 4. Tipos de pregunta (`kind`)

Los siguientes valores de `kind` están soportados en la versión 1:

| `kind`                   | Descripción                                                     | Estructura `content`                                                   |
|--------------------------|-----------------------------------------------------------------|------------------------------------------------------------------------|
| `single_choice`          | Selección de una opción.                                        | `options[]`, `correct[]` (0‑1), `user[]` (0‑1).                        |
| `multi_select`           | Selección de varias opciones.                                   | `options[]`, `correct[]`, `user[]`.                                    |
| `matching`               | Emparejamiento de elementos.                                    | `pairs_user[]`, `pairs_correct[]`, `domain_hint` opcional.             |
| `short_answer_text`      | Respuesta corta de texto (una palabra/frase).                    | `expected[]`, `user` (string/null).                                    |
| `numeric`                | Respuesta numérica con posible formato específico.              | `expected[]`, `user` (string/null), `numeric_format{decimal_separator, round_decimals, tolerance}`. |
| `cloze_labeled_blanks`   | Rellenar huecos etiquetados (`TP`, `TN`, `a`, `b`, …).           | `blanks[]` (cada uno con `label`, `expected`, `user`).                |
| `cloze_table`            | Completar una tabla.                                            | `table` (objeto o null; si null se proveen assets).                   |
| `multipart_short_answer` | Pregunta compuesta con subapartados numerados (1., 2., …).      | `items[]` (cada uno con `index`, `prompt`, `expected`, `user`, `subitems[]`). |
| `external_media_reference`| Pregunta que depende de un recurso externo (vídeo).             | `reference_text` con la descripción del recurso.                       |

El campo `options` para `single_choice` y `multi_select` contiene una lista de objetos con clave `key` (letra a–e) y `text` con el texto de la opción. Los campos `correct` y `user` son arrays de claves seleccionadas.

El campo `pairs_user` para `matching` es un array de pares `{left, right}` con las parejas marcadas por el usuario; `pairs_correct` contiene las correctas.

Para `numeric`, el subobjeto `numeric_format` indica:
- `decimal_separator`: coma `,` o punto `.` según el enunciado.
- `round_decimals`: número de decimales que se solicita redondear (o null si no se menciona).
- `tolerance`: margen de error aceptable (o null).

Para `multipart_short_answer`, cada `item` puede contener `subitems[]` cuando dentro del mismo apartado hay subcampos etiquetados (p.ej. `A: …`, `B: …`). Se reutiliza la estructura de blanks etiquetados (`label`, `expected`, `user`).

## 5. Assets (`stem.assets[]`)

Cualquier objeto de tipo `Asset` tiene los siguientes campos:

| Campo    | Tipo     | Descripción                                                     |
|---------|----------|-----------------------------------------------------------------|
| `type`  | string   | Puede ser `full_page` o `page_clip`. En v1 se usa `full_page`. |
| `page`  | integer  | Índice (0‑based) de la página donde se captura el asset.        |
| `bbox`  | array o null | Coordenadas `[x0, y0, x1, y1]` si se trata de un clip; null en full page. |
| `file`  | string   | Ruta relativa al archivo de imagen generado.                   |

## 6. Incidencias (`issues[]`)

Los códigos de incidencia y su significado se detallan en `RULES_v1.md`. Las incidencias sirven para señalar pérdidas de información, detección de penalizaciones, estructuras no reconocidas, etc. Deben registrarse tanto a nivel de pregunta (`Question.issues`) como de documento (`ExamDoc.issues`), según corresponda.
