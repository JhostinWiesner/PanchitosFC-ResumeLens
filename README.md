# PanchitosFC - ResumeLens

## Contents

- [Overview](#overview)
- [Documentation index](#documentation-index)
- [Pipeline and formal models](#pipeline-and-formal-models)
- [Design decisions](#design-decisions)
- [Supported profiles](#supported-profiles)
- [Canonical catalog](#canonical-catalog)
- [Input format, assumptions, and limitations](#input-format-assumptions-and-limitations)
- [Project structure](#project-structure)
- [Running the project](#running-the-project)
- [Tests](#tests)
- [Git workflow and team](#git-workflow-and-team)

## Overview

The same qualification can be written in several ways in a résumé, such as
`JS`, `Javascript`, and `ECMAScript`. At the same time, each professional
profile requires a different combination and order of qualification categories.

ResumeLens extracts qualifications explicitly found in a plain-text résumé,
checks whether they satisfy a formally defined pattern for a selected
professional profile, and produces a validated HTML candidate profile. It does
not rank candidates or make hiring decisions.

## Documentation index

| Document | What it covers | Link |
|---|---|---|
| Stage 1 extraction | Section detection, regular expressions, extraction contract, and recognized headers | [`docs/stage1_extraction.md`](docs/stage1_extraction.md) |
| Stage 2 normalization | The catalog-driven finite-state transducer and canonical qualification names | [`docs/stage2_normalization.md`](docs/stage2_normalization.md) |
| Stage 2 ordering | Profile filtering, duplicate removal, and canonical ordering | [`docs/stage2_ordering.md`](docs/stage2_ordering.md) |
| Stage 3 recognition | Profile DFAs, states, transitions, and recognized languages | [`docs/stage3_recognition.md`](docs/stage3_recognition.md) |
| Stage 1 test design | Extraction scenarios and expected results | [`docs/test_design/stage1_extraction_test_cases.md`](docs/test_design/stage1_extraction_test_cases.md) |
| Stage 2 test design | Normalization and ordering scenarios and expected results | [`docs/test_design/stage2_normalization_ordering_test_cases.md`](docs/test_design/stage2_normalization_ordering_test_cases.md) |
| Stage 3 test design | Recognition scenarios and expected results | [`docs/test_design/stage3_recognition_test_cases.md`](docs/test_design/stage3_recognition_test_cases.md) |
| Stage 4 test design | Candidate-profile grammar, validation, round trips, and HTML-related cases | [`docs/test_design/stage4_profile_test_cases.md`](docs/test_design/stage4_profile_test_cases.md) |
| Candidate-profile grammar | The textX grammar for candidate profiles | [`core/grammar/candidate.tx`](core/grammar/candidate.tx) |
| Canonical catalog | Profiles, categories, canonical names, aliases, and eligibility | [`core/catalog.json`](core/catalog.json) |
| Sample résumés | Plain-text inputs covering supported profiles and edge cases | [`samples/`](samples/) |
| Installation dependencies | Python packages required to run the application and tests | [`requirements.txt`](requirements.txt) |

The repository does not contain `GIT_WORKFLOW.md`; consequently, there is no
repository file to link for Git workflow instructions.

## Pipeline and formal models

| Stage | Formal model | Tool | Main module | Documentation link |
|---|---|---|---|---|
| 1. Extraction | Regular expressions | Python `re` | [`core/extraction.py`](core/extraction.py) | [`stage1_extraction.md`](docs/stage1_extraction.md) |
| 2. Normalization and ordering | Finite-state transducer, followed by profile-specific ordering | `pyformlang` | [`core/normalization.py`](core/normalization.py) and [`core/ordering.py`](core/ordering.py) | [`stage2_normalization.md`](docs/stage2_normalization.md), [`stage2_ordering.md`](docs/stage2_ordering.md) |
| 3. Recognition | Deterministic finite automaton | `pyformlang` | [`core/recognition.py`](core/recognition.py) | [`stage3_recognition.md`](docs/stage3_recognition.md) |
| 4. Candidate profile language | Context-free grammar and validated model | `textX` | [`core/grammar/grammar.py`](core/grammar/grammar.py) and [`core/grammar/candidate.tx`](core/grammar/candidate.tx) | [`stage4_profile_test_cases.md`](docs/test_design/stage4_profile_test_cases.md) |

The data flow is:

`résumé text → ExtractedData → NormalizedQualifications → OrderedQualifications → ClassificationResult → CandidateProfile → DSL text → validated textX model → HTML`.

[`run`](pipeline.py) receives the résumé text, a `Profile`, and a validated
`Catalog`. It executes all four stages and returns a `PipelineResult` containing
the extracted data, normalized and ordered qualifications, classification,
candidate profile, generated DSL text, and rendered HTML.

## Design decisions

### Stage 1: permissive extraction

- The extractor works at the raw-text level with Python regular expressions.
- It assumes semi-structured UTF-8 plain text whose sections are introduced by
  recognizable headers.
- Recognized headers are `Professional Summary`, `Profile Summary`, `Summary`,
  `Professional Profile`, `Profile`; `Technical Skills`, `Skills`,
  `Technologies`, `Tech Stack`; `Professional Experience`, `Work Experience`,
  `Experience`, `Employment`; and `Academic Background`, `Academic
  Qualifications`, `Education`.
- Extraction preserves qualification candidates as written. It does not decide
  equivalence or profile membership.

These choices and the extraction contract are documented in
[`docs/stage1_extraction.md`](docs/stage1_extraction.md).

### Stage 2: normalization and ordering

- A single global transducer is built as a trie over all spellings in the
  catalog. An end-of-input marker (`#`) is required because some spellings are
  prefixes of others.
- The input alphabet is the characters of normalized spellings plus the marker;
  the output alphabet is the canonical qualification names, emitted as one
  symbol.
- Case folding, Unicode NFKC normalization, and whitespace collapsing happen
  before transduction. Internal punctuation is not removed.
- Ordering removes repeated qualifications, keeps only qualifications eligible
  for the selected profile, and sorts them by the profile's category order and
  then by catalog position.

See [`docs/stage2_normalization.md`](docs/stage2_normalization.md) and
[`docs/stage2_ordering.md`](docs/stage2_ordering.md).

### Stage 3: recognition

- Each profile has one DFA built by the same generic builder from the catalog
  and that profile's category order.
- The alphabet is the qualifications marked for that profile.
- The DFA has one state per category plus the initial state. It accepts one or
  more qualifications from every category, in order; repeated qualifications
  from the current category are allowed.
- Missing transitions lead to an implicit rejecting state.

The formal construction is described in
[`docs/stage3_recognition.md`](docs/stage3_recognition.md).

### Stage 4: candidate profile language

- The domain-specific language is defined by the
  [`textX` grammar](core/grammar/candidate.tx).
- Free text is quoted. Email addresses, skill names, and results are typed
  terminals.
- The flow is candidate profile → DSL text → textX validation → HTML.
- HTML output escapes every rendered value with `html.escape(..., quote=True)`.

The grammar and its executable cases are linked from
[`core/grammar/candidate.tx`](core/grammar/candidate.tx) and
[`docs/test_design/stage4_profile_test_cases.md`](docs/test_design/stage4_profile_test_cases.md).

## Supported profiles

| Identifier | Display name | Category order | Owner |
|---|---|---|---|
| `FULL_STACK` | Full Stack Developer | `LANGUAGE → FRONTEND → BACKEND → DATABASE → VCS` | Jhostin Wiesner |
| `ML_ENGINEER` | Machine Learning Engineer | `LANGUAGE → DATABASE → ML_LIBRARY → VCS` | Juan Felipe Correa |
| `DEVOPS` | DevOps Engineer | `LANGUAGE → CONTAINER → CI_CD → IAC → CLOUD → VCS` | Juan Felipe Correa |
| `DATA_ENGINEER` | Data Engineer | `LANGUAGE → DATABASE → DATA_PROCESSING → WORKFLOW → CLOUD → VCS` | Juan Diego Garcés |

The identifiers and category orders are defined in
[`profiles/`](profiles/); the owners are retained from the current README.

## Canonical catalog

[`core/catalog.json`](core/catalog.json) contains the canonical qualification
name, category, aliases, and eligible profiles. `Catalog.from_json()` validates
the JSON structure, profile identifiers, canonical-name format, required
fields, duplicate entries, profile references, and conflicting spellings before
indexing it.

To add a qualification, add one entry to the `qualifications` list with a
unique uppercase underscore-form canonical name, its category, a list of
non-empty aliases, and one or more defined profile identifiers. Keep aliases
unambiguous, then run the catalog and pipeline tests. The catalog's file order
also supplies the tie-break position used by ordering.

## Input format, assumptions, and limitations

- The application accepts `.txt` résumés and decodes them as UTF-8 (including a
  leading UTF-8 BOM). Line endings are normalized.
- Skills are extracted only inside a recognized skills section. A header may be
  alone on its line or followed by content after a colon.
- The name is searched for among the first five lines before the first
  recognized section header. Contact patterns cover email, phone, labeled or
  inline locations, LinkedIn, and GitHub.
- Summary text is taken from an explicit summary section or from non-contact
  text after the detected name and before the first recognized section.
- Education is collected one non-empty line at a time. Experience entries use
  recognized date ranges as anchors when available, with non-empty
  blank-line-separated blocks as a fallback.
- Text outside recognized sections is not searched for qualifications. Unknown
  skill candidates are retained as unrecognized diagnostics, while recognized
  qualifications are filtered and deduplicated during ordering.
- Recognition requires at least one qualification from every category in the
  selected profile and requires the resulting sequence to be in category order.

These assumptions and edge cases are detailed in
[`docs/stage1_extraction.md`](docs/stage1_extraction.md),
[`docs/stage2_ordering.md`](docs/stage2_ordering.md), and
[`docs/stage3_recognition.md`](docs/stage3_recognition.md).

## Project structure

```text
.
├── app.py                         # Streamlit user interface
├── pipeline.py                    # Four-stage pipeline orchestrator
├── requirements.txt               # Pinned Python dependencies
├── core/
│   ├── catalog.json               # Canonical qualification catalog
│   ├── catalog.py                 # Catalog loading and validation
│   ├── extraction.py              # Stage 1: regular-expression extraction
│   ├── normalization.py           # Stage 2: catalog transducer
│   ├── ordering.py                # Stage 2: profile filtering and ordering
│   ├── recognition.py              # Stage 3: profile DFA recognition
│   ├── text.py                    # Text normalization helpers
│   ├── types.py                   # Typed data contracts
│   └── grammar/
│       ├── candidate.tx           # Stage 4 textX grammar
│       └── grammar.py             # DSL validation and HTML rendering
├── profiles/
│   ├── base.py                    # Shared profile data contract
│   ├── full_stack.py              # Full Stack profile
│   ├── ml_engineer.py             # Machine Learning Engineer profile
│   ├── dev_ops.py                 # DevOps profile
│   └── data_engineer.py           # Data Engineer profile
├── docs/
│   ├── stage1_extraction.md       # Stage 1 documentation
│   ├── stage2_normalization.md    # Stage 2 normalization documentation
│   ├── stage2_ordering.md         # Stage 2 ordering documentation
│   ├── stage3_recognition.md      # Stage 3 documentation
│   ├── assets/                    # Diagrams for the normalization documentation
│   └── test_design/               # Test-case design documents
├── samples/                       # Sample plain-text résumés
└── tests/                         # Automated tests
```

## Running the project

From the repository root, install the dependencies:

```bash
pip install -r requirements.txt
```

Start the Streamlit application:

```bash
streamlit run app.py
```

Upload a UTF-8 `.txt` résumé, choose one of the four supported profiles, and
select **Evaluate résumé**. The app displays whether the résumé is accepted,
embeds the generated HTML candidate profile, and offers an HTML download.

Run the test suite from the repository root:

```bash
pytest tests/
```

The [`samples/`](samples/) folder contains ten plain-text résumé inputs:
profile examples for Full Stack, Data Engineer, DevOps, and Machine Learning
Engineer, plus cases for unknown skills, duplicates, minimal sections, no
recognized skills, HTML escaping, and a résumé containing qualifications for
all profiles.

## Tests

| Test file | Coverage | Test design |
|---|---|---|
| [`tests/test_extraction.py`](tests/test_extraction.py) | Names, contact fields, summaries, section aliases, line endings, skills, education, experience, and invalid input | [`stage1_extraction_test_cases.md`](docs/test_design/stage1_extraction_test_cases.md) |
| [`tests/test_normalization.py`](tests/test_normalization.py) | Catalog spellings, aliases, unknown candidates, duplicates, blanks, and empty input | [`stage2_normalization_ordering_test_cases.md`](docs/test_design/stage2_normalization_ordering_test_cases.md) |
| [`tests/test_ordering.py`](tests/test_ordering.py) | Profile filtering, duplicate removal, category order, immutability, and unknown canonical names | [`stage2_normalization_ordering_test_cases.md`](docs/test_design/stage2_normalization_ordering_test_cases.md) |
| [`tests/test_recognition.py`](tests/test_recognition.py) | DFA structure, documented sequences, missing categories, unordered input, foreign symbols, and empty groups | [`stage3_recognition_test_cases.md`](docs/test_design/stage3_recognition_test_cases.md) |
| [`tests/test_grammar.py`](tests/test_grammar.py) | Candidate DSL validity, invalid documents, round trips, typed terminals, free text, and non-ASCII values | [`stage4_profile_test_cases.md`](docs/test_design/stage4_profile_test_cases.md) |
| [`tests/test_catalog.py`](tests/test_catalog.py) | Catalog loading, normalization, ordering metadata, aliases, conflicts, and validation errors | [`stage2_normalization_ordering_test_cases.md`](docs/test_design/stage2_normalization_ordering_test_cases.md) |
| [`tests/test_pipeline_integration.py`](tests/test_pipeline_integration.py) | End-to-end extraction, normalization, recognition, deduplication, and HTML escaping | [`stage4_profile_test_cases.md`](docs/test_design/stage4_profile_test_cases.md) |

## Git workflow and team

The requested `GIT_WORKFLOW.md` file is not present in this repository, so no
Git workflow document can be linked.

| Profile | Owner |
|---|---|
| Full Stack Developer | Jhostin Wiesner |
| Machine Learning Engineer | Juan Felipe Correa |
| DevOps | Juan Felipe Correa |
| Data Engineer | Juan Diego Garcés |
