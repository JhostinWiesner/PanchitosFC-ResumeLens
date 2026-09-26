# PanchitosFC - ResumeLens

ResumeLens procesa currículums en texto plano y determina si las calificaciones identificadas satisfacen los patrones formales definidos para un perfil profesional, aplicando expresiones regulares, transductores de estados finitos, autómatas finitos y gramáticas libres de contexto en un mismo pipeline compartido.

## Perfiles soportados

| Perfil | Responsable |
|---|---|
| Full Stack Developer | Jhostin Wiesner |
| Machine Learning Engineer | Juan Diego Garcés |
| _____________ (propio, software engineering) | Juan Felipe Correa |
| _____________ (propio, AI/data) | Juan Felipe Correa |

> Los 4 perfiles corren sobre **la misma solución de software genérica** — ver `profiles/base.py`. Ningún perfil tiene una implementación de pipeline aislada.

## Stack técnico

- **UI**: Streamlit
- **Extracción (Stage 1)**: `re` (módulo estándar de Python)
- **Normalización (Stage 2)**: `pyformlang` (transductores de estados finitos)
- **Reconocimiento (Stage 3)**: `pyformlang` (`FiniteAutomaton`)
- **Gramática de perfil de candidato (Stage 4)**: `textX`

## Estructura del proyecto

```
resumelens/
├── app.py                      # Entry point de Streamlit
├── core/
│   ├── extraction.py            # Stage 1 — regex
│   ├── normalization.py         # Stage 2 — FST
│   ├── recognition.py           # Stage 3 — autómatas
│   └── grammar/
│       ├── candidate.tx         # Gramática textX
│       └── grammar.py           # Carga del modelo + validación + visualización
├── profiles/
│   ├── base.py                  # Clase Profile (contrato común)
│   ├── full_stack.py
│   ├── ml_engineer.py
│   ├── profile_own_1.py
│   └── profile_own_2.py
├── pipeline.py                  # Orquestador: corre las 4 etapas en orden
└── tests/
    ├── test_extraction.py
    ├── test_normalization.py
    ├── test_recognition.py
    └── test_grammar.py
```

## Arquitectura del pipeline

Cada etapa recibe y entrega una `dataclass` tipada — ningún dato intermedio se pasa como diccionario suelto:

1. **`extract(resume_text) -> ExtractedData`** — información cruda extraída por regex (contacto, resumen y experiencia se extraen literal del texto, sin reescritura).
2. **`normalize(data, profile) -> NormalizedQualifications`** — calificaciones transformadas a su forma canónica y ordenadas según `profile.canonical_order`.
3. **`recognize(normalized, profile) -> ClassificationResult`** — evalúa contra el `FiniteAutomaton` del perfil; la explicación del resultado (ACCEPTED/REJECTED) se arma con **plantilla fija por perfil**.
4. **`build_candidate_profile(...) -> CandidateProfile`** — estructura todo lo anterior según la gramática textX y genera la visualización HTML/Markdown final.

El objeto `Profile` (`profiles/base.py`) es lo único que cambia entre perfiles: nombre, orden canónico, reglas del FST, y el autómata de patrón aceptado. `pipeline.py` no contiene lógica específica de ningún perfil.

## Cómo correr el proyecto

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Cómo correr los tests

```bash
pytest tests/
```

## Convenciones de nombres canónicos

_(completar aquí una vez que el equipo cierre esta tarea — ver tarjeta correspondiente en Trello)_

## Estado del proyecto

Ver el tablero de Trello del equipo para el estado de cada etapa por perfil.