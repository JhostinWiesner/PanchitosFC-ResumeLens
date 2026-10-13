# PanchitosFC - ResumeLens

ResumeLens addresses the fact that the same qualification can be written in many ways, while each professional profile requires a different combination of qualifications. It checks whether qualifications explicitly found in a plain-text résumé satisfy a formally defined pattern for a chosen profile and produces a validated HTML profile. It does not rank candidates or make hiring decisions.

**Live demo:** [ResumeLens on Streamlit](https://panchitos-fc.streamlit.app/). To try it, upload one of the résumés in [`samples/`](samples/).

## Pipeline

| Stage | Formal model | Tool | Module | Documentation |
|---|---|---|---|---|
| 1. Extraction | Regular expressions | Python `re` | [`core/extraction.py`](core/extraction.py) | [`stage1_extraction.md`](docs/stage1_extraction.md) |
| 2. Normalization and ordering | Finite-state transducer and profile ordering | `pyformlang` | [`core/normalization.py`](core/normalization.py), [`core/ordering.py`](core/ordering.py) | [`stage2_normalization.md`](docs/stage2_normalization.md), [`stage2_ordering.md`](docs/stage2_ordering.md) |
| 3. Recognition | Deterministic finite automaton | `pyformlang` | [`core/recognition.py`](core/recognition.py) | [`stage3_recognition.md`](docs/stage3_recognition.md) |
| 4. Candidate profile language | Context-free grammar | `textX` | [`core/grammar/grammar.py`](core/grammar/grammar.py), [`core/grammar/candidate.tx`](core/grammar/candidate.tx) | [`stage4_grammar.md`](docs/stage4_grammar.md) |

Test scenarios are documented in [`docs/test_design/`](docs/test_design/);
qualifications and profile eligibility are defined in
[`core/catalog.json`](core/catalog.json).

## Key design decisions

- **Stage 1:** permissive extraction from semi-structured résumé sections; it does not decide equivalence or profile membership ([details](docs/stage1_extraction.md)).
- **Stage 2:** one catalog-wide trie transducer maps normalized spellings to canonical names, then ordering filters, deduplicates, and sorts by profile category ([normalization](docs/stage2_normalization.md), [ordering](docs/stage2_ordering.md)).
- **Stage 3:** one generic DFA per profile requires at least one qualification from every category in the declared order ([details](docs/stage3_recognition.md)).
- **Stage 4:** quoted free text and typed terminals form a textX DSL that is validated before HTML rendering ([grammar and validation](docs/stage4_grammar.md)).

## Profiles

| Profile | Category order | 
|---|---|
| Full Stack Developer | `LANGUAGE → FRONTEND → BACKEND → DATABASE → VCS` |
| Machine Learning Engineer | `LANGUAGE → DATABASE → ML_LIBRARY → VCS` |
| DevOps Engineer | `LANGUAGE → CONTAINER → CI_CD → IAC → CLOUD → VCS` |
| Data Engineer | `LANGUAGE → DATABASE → DATA_PROCESSING → WORKFLOW → CLOUD → VCS` |

## Catalog, input, and limitations

The canonical catalog is [`core/catalog.json`](core/catalog.json); add a qualification there with a unique canonical name, category, aliases, and defined profile identifiers ([catalog design](docs/stage2_normalization.md)).

The app accepts UTF-8 plain-text `.txt` résumés. Skills are searched inside recognized résumé sections; see the [recognized headers and extraction contract](docs/stage1_extraction.md).

Important limitations: unrecognized-section text is not searched for skills; recognition requires every category in the selected profile; and the input sequence must follow the profile's category order. See the [extraction](docs/stage1_extraction.md), [ordering](docs/stage2_ordering.md), and [recognition](docs/stage3_recognition.md)
documentation for the remaining cases.

## Running

From the repository root:

```bash
pip install -r requirements.txt
streamlit run app.py
python -m pytest tests/
```

The app evaluates an uploaded résumé and displays the acceptance result, validated HTML profile, and an HTML download. [`samples/`](samples/) contains ten plain-text profile examples and edge-case inputs.

## Project structure

```text
.
├── app.py                 # Streamlit entry point
├── pipeline.py            # Pipeline orchestrator
├── requirements.txt       # Python dependencies
├── core/                  # Catalog, pipeline stages, types, and grammar
│   └── grammar/           # textX grammar and serializer/renderer
├── profiles/              # Shared profile definitions
├── docs/                  # Formal stage and test-design documentation
│   ├── assets/            # Normalization diagrams
│   └── test_design/       # Test-case specifications
├── samples/               # Sample résumé inputs
└── tests/                 # Automated test suite
```
