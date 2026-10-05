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
│   ├── profile_own_1.py
│   └── profile_own_2.py
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

The `Profile` object (`profiles/base.py`) is the only thing that changes between profiles: name, canonical order, FST rules, and the accepted pattern automaton. `pipeline.py` does not contain any profile-specific logic.

## How to run the project

```bash
pip install -r requirements.txt
streamlit run app.py
```

## How to run the tests

```bash
pytest tests/
```

## Canonical names configuration


Catalog shared by the 4 profiles. It is read by Stage 1 (extraction), Stage 2 (normalization), and each `Profile`, ensuring the pipeline remains free of profile-specific logic.

**Profiles:** FS = Full Stack Developer · ML = Machine Learning Engineer · DO = DevOps Engineer · DE = Data Engineer

---

### 1. Naming rules

| Rule | Example |
|---|---|
| `UPPERCASE_WITH_UNDERSCORES`, ASCII only | `NODE_JS`, `SCIKIT_LEARN` |
| No dots, `+`, `#`, or spaces | `C++` → `CPP`, `C#` → `C_SHARP` |
| No version numbers | `Python3` → `PYTHON` |
| Official English name | `POSTGRESQL`, not `POSTGRES` |
| Aliases are not canonical names | `JS`, `Javascript` → `JAVASCRIPT` |
| Each name belongs to **exactly one category** | `GIT` → `VCS` |

---

### 2. Global catalog

The row order within each category serves as the **tie-breaker** for `order()`.

| Canonical | Category | Aliases | FS | ML | DO | DE |
|---|---|---|:-:|:-:|:-:|:-:|
| `JAVASCRIPT` | `LANGUAGE` | JS, ​​Javascript, ECMAScript | ✓ | | | |
| `TYPESCRIPT` | `LANGUAGE` | TS | ✓ | | | |
| `PYTHON` | `LANGUAGE` | py, Python3 | | ✓ | ✓ | ✓ |
| `BASH` | `LANGUAGE` | Shell, Shell scripting, sh | | | ✓ | |
| `GO` | `LANGUAGE` | Golang | | | ✓ | |
| `REACT` | `FRONTEND` | React.js, ReactJS | ✓ | | | |
| `ANGULAR` | `FRONTEND` | Angular.js, AngularJS | ✓ | | | |
| `VUE` | `FRONTEND` | Vue.js, VueJS | ✓ | | | |
| `NODE_JS` | `BACKEND` | NodeJS, Node.js, Node | ✓ | | | |
| `DJANGO` | `BACKEND` | | ✓ | | | |
| `SPRING_BOOT` | `BACKEND` | Spring, SpringBoot | ✓ | | | |
| `REST_API` | `BACKEND` | REST, RESTful | ✓ | | | |
| `SQL` | `DATABASE` | | ✓ | ✓ | | ✓ |
| `POSTGRESQL` | `DATABASE` | Postgres, psql | ✓ | ✓ | | ✓ |
| `MONGODB` | `DATABASE` | Mongo | ✓ | | | ✓ |
| `MYSQL` | `DATABASE` | | | | | ✓ |
| `SNOWFLAKE` | `DATABASE` | | | | | ✓ |
| `PANDAS` | `ML_LIBRARY` | | | ✓ | | |
| `NUMPY` | `ML_LIBRARY` | | | ✓ | | |
| `SCIKIT_LEARN` | `ML_LIBRARY` | sklearn, scikit-learn | | ✓ | | |
| `TENSORFLOW` | `ML_LIBRARY` | TF | | ✓ | | |
| `PYTORCH` | `ML_LIBRARY` | torch | | ✓ | | |
| `SPARK` | `DATA_PROCESSING` | Apache Spark, PySpark | | | | ✓ |
| `KAFKA` | `DATA_PROCESSING` | Apache Kafka | | | | ✓ |
| `HADOOP` | `DATA_PROCESSING` | Apache Hadoop | | | | ✓ |
| `DBT` | `DATA_PROCESSING` | dbt | | | | ✓ |
| `AIRFLOW` | `WORKFLOW` | Apache Airflow | | | | ✓ |
| `DOCKER` | `CONTAINER` | Docker Compose | | | ✓ | |
| `KUBERNETES` | `CONTAINER` | K8s, kube | | | ✓ | |
| `JENKINS` | `CI_CD` | | | | ✓ | |
| `GITHUB_ACTIONS` | `CI_CD` | GH Actions, Github Actions | | | ✓ | |
| `GITLAB_CI` | `CI_CD` | GitLab CI/CD | | | ✓ | |
| `TERRAFORM` | `IAC` | | | | ✓ | |
| `ANSIBLE` | `IAC` | | | | ✓ | |
| `AWS` | `CLOUD` | Amazon Web Services | | | ✓ | ✓ |
| `GCP` | `CLOUD` | Google Cloud, Google Cloud Platform | | | ✓ | ✓ |
| `AZURE` | `CLOUD` | Microsoft Azure | | | ✓ | ✓ |
| `GIT` | `VCS` | | ✓ | ✓ | ✓ | ✓ |

`IAC` = *Infrastructure as Code*. `CI_CD` = Continuous Integration and Continuous Delivery.

> The FS and ML origins represent the baseline proposal; those responsible for these profiles must confirm it.

---

### 3. Canonical category order by profile

| Profile | Canonical order |
|---|---|
| Full Stack Developer | `LANGUAGE → FRONTEND → BACKEND → DATABASE → VCS` |
| Machine Learning Engineer | `LANGUAGE → ML_LIBRARY → DATABASE → VCS` |
| DevOps Engineer | `LANGUAGE → CONTAINER → CI_CD → IAC → CLOUD → VCS` |
| Data Engineer | `LANGUAGE → DATABASE → DATA_PROCESSING → WORKFLOW → CLOUD → VCS` |

Team convention: `LANGUAGE` first and `VCS` always last.

#### Qualifications by profile and category

**Full Stack Developer**
- `LANGUAGE`: JAVASCRIPT, TYPESCRIPT
- `FRONTEND`: REACT, ANGULAR, VUE
- `BACKEND`: NODE_JS, DJANGO, SPRING_BOOT, REST_API
- `DATABASE`: SQL, POSTGRESQL, MONGODB
- `VCS`: GIT

**Machine Learning Engineer**
- `LANGUAGE`: PYTHON
- `ML_LIBRARY`: PANDAS, NUMPY, SCIKIT_LEARN, TENSORFLOW, PYTORCH
- `DATABASE`: SQL, POSTGRESQL
- `VCS`: GIT

**DevOps Engineer**
- `LANGUAGE`: PYTHON, BASH, GO
- `CONTAINER`: DOCKER, KUBERNETES
- `CI_CD`: JENKINS, GITHUB_ACTIONS, GITLAB_CI
- `IAC`: TERRAFORM, ANSIBLE
- `CLOUD`: AWS, GCP, AZURE
- `VCS`: GIT

**Data Engineer**
- `LANGUAGE`: PYTHON
- `DATABASE`: SQL, POSTGRESQL, MONGODB, MYSQL, SNOWFLAKE
- `DATA_PROCESSING`: SPARK, KAFKA, HADOOP, DBT
- `WORKFLOW`: AIRFLOW
- `CLOUD`: AWS, GCP, AZURE
- `VCS`: GIT

---

### 4. Ordering rules (`order()`)

1. **Tie-breaking within a category:** the order in which qualifications appear in the global catalog (section 2) is used, not the order in which the candidate wrote them.
2. **Categories not used by the profile:** `order()` **ignores** them for that profile. ResumeLens evaluates whether a pattern is met; it does not penalize the candidate for having other skills. ### Examples

#### Examples

| Profile       | Input                                                      | Sorted Output                                             |
|---------------|------------------------------------------------------------|-----------------------------------------------------------|
| Full Stack    | `Git, NodeJS, JS, Postgres, React.js`                      | `JAVASCRIPT, REACT, NODE_JS, POSTGRESQL, GIT`             |
| ML Engineer   | `Git, PostgreSQL, TensorFlow, Pandas, Python`              | `PYTHON, PANDAS, TENSORFLOW, POSTGRESQL, GIT`             |
| DevOps        | `Terraform, Git, Docker, AWS, Python, Jenkins, Kubernetes` | `PYTHON, DOCKER, KUBERNETES, JENKINS, TERRAFORM, AWS, GIT` |
| Data Engineer | `Airflow, Git, Spark, PostgreSQL, Python, AWS`             | `PYTHON, POSTGRESQL, SPARK, AIRFLOW, AWS, GIT`            |

---

## 5. Pending Items to Confirm with the Team

- Confirm that the Full Stack and ML Engineer teams approve the proposed categories and ordering for their profiles.
- Decide whether `PYSPARK` should remain as an alias for `SPARK` or be treated as a separate category.
- Define the catalog file format (for example, `core/catalog.json`) and its location in the repository.
