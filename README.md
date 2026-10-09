# PanchitosFC - ResumeLens

ResumeLens processes plain-text resumes and determines whether the identified qualifications meet the formal criteria defined for a professional profile, applying regular expressions, finite-state transducers, finite automata, and context-free grammars within a single shared pipeline.

## Supported profiles

| Perfil | Responsable |
|---|---|
| Full Stack Developer | Jhostin Wiesner |
| Machine Learning Engineer | Juan Diego Garcés |
| DevOps | Juan Felipe Correa |
| Data Engineer | Juan Felipe Correa |

> All 4 profiles run on **the same generic software solution** — see `profiles/base.py`. No profile has an isolated pipeline implementation.

## Technologies used

- **UI**: Streamlit
- **Extraction (Stage 1)**: `re` (Python standard module)
- **Normalization (Stage 2)**: `pyformlang` (finite-state transducers)
- **Recognition (Stage 3)**: `pyformlang` (`FiniteAutomaton`)
- **Candidate profile grammar (Stage 4)**: `textX`

## Project structure

```
resumelens/
├── app.py                      # Streamlit entry point
├── core/
|   ├── catalog.json 
|   ├── catalog.py 
|   ├── text.py 
|   ├── types.py                 # Typed dataclasses for each stage
│   ├── extraction.py            # Stage 1 — regex
│   ├── normalization.py         # Stage 2 — FST
│   ├── recognition.py           # Stage 3 — automata
│   └── grammar/
│       ├── candidate.tx         # textX grammar
│       └── grammar.py           # Model upload + validation + visualization
├── profiles/
│   ├── base.py                  # Profile base class (common contract)
│   ├── full_stack.py
│   ├── ml_engineer.py
│   ├── dev_ops.py
│   └── data_engineer.py
├── pipeline.py                  # Ochestrator: runs all stages in order
└── tests/
    ├── test_extraction.py
    ├── test_normalization.py
    ├── test_recognition.py
    └── test_grammar.py
```

## Pipeline architecture

Each stage receives and returns a typed `dataclass`—no intermediate data is passed as a standalone dictionary:

1. **`extract(resume_text) -> ExtractedData`** — raw information extracted using regular expressions (contact information, summary, and experience are extracted verbatim from the text, without rewriting).
2. **`normalize(extracted) -> NormalizedQualifications`** — qualifications transformed into their canonical form.
3. **`order(normalized, profile) -> OrderedQualifications`** — qualifications ordered according to `profile.canonical_order`.
4. **`recognize(ordered, profile) -> ClassificationResult`** — evaluates against the profile’s `FiniteAutomaton`; the explanation for the result (ACCEPTED/REJECTED) is constructed using a **fixed template per profile**.
5. **`build_candidate_profile(...) -> CandidateProfile`** — structures all of the above according to the textX grammar and generates the final HTML/Markdown visualization.

The `Profile` object (`profiles/base.py`) is the only thing that changes between profiles: its name, canonical order, accepted-pattern automaton, and result explanation template. Extraction and normalization are global and independent of the profile, and `pipeline.py` does not contain any profile-specific logic.

## Input format

ResumeLens expects résumés as plain text (UTF-8). Line endings are normalized to `\n` on input. The extractor assumes a semi-structured résumé whose sections are introduced by a recognizable header on its own line (for example `Skills`, `Experience`, `Education`); sections without a recognized header are not extracted. See `docs/stage1-extraction.md` for the supported headers and the formal definition of each expression.



## How to run the project

```bash
pip install -r requirements.txt
streamlit run app.py
```

## How to run the tests

```bash
pytest tests/
```
