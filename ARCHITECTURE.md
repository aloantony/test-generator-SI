# Arquitectura del proyecto

Este documento describe la arquitectura del pipeline, los módulos internos y las APIs previstas para la versión 1 del proyecto *Creador de tests*. La implementación se organiza de forma modular para facilitar la evolución del sistema.

## 1. Visión general del pipeline

El procesamiento de un PDF se realiza en varias etapas secuenciales:

1. **Extracción de texto con layout** (`pdf.extract`):
   - Se utilizan bibliotecas como PyMuPDF para extraer bloques de texto y su posición en cada página.
   - Se eliminan encabezados y pies repetidos.

2. **Normalización** (`core.normalize`):
   - Se unifican espacios, saltos de línea y codificaciones.
   - Se corrigen numeraciones y caracteres Unicode extraños.

3. **Segmentación** (`pdf.segment`):
   - Se agrupan las líneas en **QuestionBlocks** empleando los delimitadores primarios (`^Pregunta N`) y secundarios (ver `RULES_v1.md`).

4. **Tipado** (`parse.typify`):
   - Se determina el `kind` de cada bloque aplicando reglas de detección en orden de prioridad.

5. **Extracción específica** (`parse.extract_*`):
   - Según el `kind`, se invoca al extractor adecuado (`extract_choice`, `extract_matching`, `extract_numeric`, etc.) para poblar el campo `content`.
   - Se recogen `issues` cuando se detectan anomalías (p.ej. opciones vacías, tablas no estructurables).

6. **Grading** (`parse.grading`):
   - Se extraen las indicaciones de corrección: estado (Correcta/Parcial/Incorrecta), puntuaciones, penalizaciones y feedback.

7. **Flags y assets** (`assets.policy` y `assets.render`):
   - Se activan flags (`asset_required`, `math_or_symbols_risky`, `requires_external_media`) según reglas definidas.
   - En v1, si `asset_required=true`, se genera un asset de página completa (`full_page`) por cada página en la que aparezca la pregunta.

8. **Validación** (`validate.schema_validate`):
   - El JSON final se valida contra el schema oficial para garantizar conformidad.

9. **Renderizadores futuros** (`renderers/html_placeholder`):
   - Se prevé la incorporación de renderizadores para HTML u otros formatos. En v1 se incluirá un stub.


## 2. Estructura de `src/`

La carpeta `src/creador_tests/` se subdivide de la siguiente manera:

- **`cli.py`**: contendrá el código de la interfaz de línea de comandos. Implementará comandos como `parse`, `validate` y `batch`.
- **`core/`**: módulos de infraestructura comunes:
  - `types.py`: definiciones de dataclasses o tipos reutilizados (p.ej. `QuestionBlock`, `ExamDoc`).
  - `issues.py`: enumeración y manejo de códigos de incidencia.
  - `normalize.py`: funciones de normalización de texto.
  - `rules_engine.py`: carga y aplicación de las reglas de tipado/flags definidas en `rules/rules-1.0.yaml`.
- **`pdf/`**: extracción y segmentación:
  - `extract.py`: extracción de texto y layout desde PDFs.
  - `segment.py`: lógica de segmentación en bloques de pregunta.
- **`parse/`**: detectores de tipo y extractores concretos:
  - `typify.py`: algoritmo de decisión para `kind`.
  - `extract_choice.py`, `extract_matching.py`, …: uno por cada tipo enumerado en `DATA_MODEL.md`.
  - `extract_multipart.py`: extractor para preguntas compuestas con subapartados.
- **`assets/`**: generación y política de assets:
  - `policy.py`: lógica que decide si es necesario un asset y su tipo.
  - `render.py`: funciones que renderizan páginas completas o clips de página.
- **`validate/`**:
  - `schema_validate.py`: encapsula la validación contra el JSON Schema.
- **`renderers/`**:
  - `html_placeholder.py`: stub para futuros renderizadores (HTML idéntico, XML, etc.).


## 3. Contrato interno de tipos (Python)

Se emplearán dataclasses o tipos similares para representar las estructuras internas. Ejemplo de algunas entidades:

```python
@dataclass
class Block:
    text: str
    page_index: int


@dataclass
class QuestionBlock:
    number: int
    pages: List[int]
    block_text: str


@dataclass
class ExamDoc:
    schema_version: str
    source: Source
    questions: List[Question]
    issues: List[Issue]
```

La definición concreta de `Question` y sus subtipos corresponde a `DATA_MODEL.md` y al Schema.


## 4. CLI (versión inicial)

Se prevé un CLI con tres subcomandos principales:

1. **`parse`**: procesa un PDF y genera un JSON + assets según el contrato v1.
   - Argumentos: `--in` ruta al PDF, `--out` ruta al JSON de salida, `--assets-out` directorio de assets.
2. **`validate`**: valida un JSON frente al schema.
   - Argumentos: `--in` ruta al JSON, `--schema` ruta al schema (por defecto, `schemas/exam_doc-1.0.schema.json`).
3. **`batch`**: procesa un directorio con múltiples PDFs.
   - Argumentos: `--in` directorio de entrada, `--out` directorio de JSON, `--assets-out` directorio de assets.

La implementación se incorporará en futuras versiones respetando los contratos definidos en este repositorio.
