# Reglas v1

Este documento describe las reglas utilizadas en la versión 1 del proyecto para segmentar, tipar y extraer información de las preguntas, así como para determinar flags, grading e incidencias. El motor de reglas se basa en el archivo YAML `rules/rules-1.0.yaml` que implementa estos criterios de forma declarativa.

## 1. Segmentación

El proceso de segmentación divide el texto extraído del PDF en bloques de pregunta. Se emplean **marcadores primarios** y **marcadores secundarios**:

- **Delimitador primario**: líneas que encajan con el patrón `^Pregunta\s+\d+\b`. Este marcador inicia un nuevo bloque de pregunta.
- **Marcadores secundarios**: cadenas que ayudan a ajustar segmentos cuando el delimitador primario se degrada o está ausente:
  - “Seleccione una:”
  - “Seleccione una o más de una:”
  - “Asocia”
  - “Respuesta:” / “Valor:”
  - “La respuesta correcta es:” / “Las respuestas correctas son:”
  - “Completa la siguiente tabla”

La segmentación final se realiza combinando estos marcadores para cubrir casos donde el encabezado no esté claramente extraído.

## 2. Tipado de preguntas (`kind`)

El tipado se realiza evaluando una serie de detectores ordenados por prioridad de mayor a menor. La detección se detiene en el primer detector que cumpla. A continuación se presentan las reglas de alto nivel (ver `rules/rules-1.0.yaml` para los patrones exactos).

1. **`multipart_short_answer`** – si dentro del bloque hay al menos dos líneas que empiezan por `^\s*\d+\.` (subapartados numerados), se trata de una pregunta compuesta.
2. **`matching`** – si el texto contiene “Asocia” o se detectan múltiples apariciones de `→` en la parte de “La respuesta correcta es:”.
3. **`multi_select`** – si aparece “Seleccione una o más de una:”.
4. **`single_choice`** – si aparece “Seleccione una:”.
5. **`cloze_table`** – si aparece “Completa la siguiente tabla”.
6. **`cloze_labeled_blanks`** – si se detectan al menos dos etiquetas seguidas de dos puntos (p.ej., `A:`, `TP:`) en líneas separadas.
7. **`external_media_reference`** – si el texto menciona “vídeo” o “video”.
8. **`numeric`** – si aparece “Respuesta:” o “Valor:” y lo que sigue es un número (con coma o punto decimal).
9. **`short_answer_text`** – si aparece “Respuesta:” y no es numérico ni encaja con otro tipo.

## 3. Flags transversales

Se activan a partir de condiciones independientes del tipo de pregunta:

- **`asset_required`**: se activa si se encuentran referencias a “figura”, “tabla de verdad”, “árbol”, “rama” o “grafo”, o si las opciones extraídas (`a.`, `b.`, …) carecen de texto significativo. También se activa cuando se detectan símbolos matemáticos/lógicos que pueden perderse en la extracción.
- **`math_or_symbols_risky`**: se activa al detectar símbolos lógicos/matemáticos como `¬`, `∧`, `∨`, `→`, `↔`, cuantificadores (`∀`, `∃`), notaciones como `\triangleq`, `\textrm`, o literales `γ`, `π`, `PDM`.
- **`requires_external_media`**: se activa cuando se detecta una referencia a un vídeo u otro recurso externo.

## 4. Grading

Se extraen los siguientes elementos del texto de la pregunta:

- **`status`**: una de `Correcta`, `Parcialmente correcta`, `Incorrecta` (o null si no aparece). Se busca en el encabezado de cada bloque.
- **`score_awarded`** y **`score_max`**: se detecta la línea con el patrón “Se puntúa X sobre Y” y se extraen ambos valores (admite números negativos y decimales con coma o punto).
- **`penalty_rule_text`**: se captura la línea donde se menciona que las respuestas incorrectas restan puntos.
- **`feedback`**: se captura cualquier frase de retroalimentación que aparezca después de la corrección, por ejemplo “¡Correcto! Efectivamente…”

## 5. Incidencias (`issues`)

Las incidencias se generan para informar de anomalías detectadas durante el parsing. Los códigos previstos en v1 son:

| Código                     | Descripción                                                             |
|---------------------------|-------------------------------------------------------------------------|
| `OPTIONS_MISSING_TEXT`    | Detectadas opciones `a./b./c./…` sin texto asociado (probable pérdida de fórmulas). |
| `MATH_TEXT_LOSS`          | Pérdida de fórmulas/notación en la extracción; se recomienda asset completo.       |
| `TABLE_STRUCTURE_LOST`    | No se ha podido reconstruir una tabla; se delega a assets.                        |
| `NO_CORRECT_ANSWER_FOUND` | No se ha encontrado el patrón de “La respuesta correcta es: …”.                   |
| `USER_ANSWER_NOT_FOUND`   | No se encuentra la respuesta del usuario en la revisión.                           |
| `EXTERNAL_MEDIA_REQUIRED` | Pregunta que requiere un recurso externo (vídeo) no disponible en el PDF.         |
| `PARTIAL_SCORING_DETECTED`| Se ha detectado corrección parcial con puntuación fraccionada.                     |

Cada incidencia se registra con un `level` (info, warn, error), un `code`, el contexto (`where`, típicamente el `id` de la pregunta) y un mensaje descriptivo.
