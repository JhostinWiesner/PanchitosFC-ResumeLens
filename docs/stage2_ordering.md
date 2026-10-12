# ResumeLens — Canonical Ordering by Profile

## 1. General Description

The canonical ordering by profile stage is responsible for organizing the technical qualifications extracted from a resume, taking into account the professional profile selected by the user from the frontend.

This stage receives the qualifications that have already been normalized by the system, removes duplicates, filters out technologies that do not correspond to the selected profile, and organizes the result using a deterministic order of categories and technologies.

The goal is to deliver a consistent list of canonical qualifications that can be used by the subsequent stages of the ResumeLens pipeline.

## 2. Location within the Pipeline

The ResumeLens pipeline is organized into the following stages:

1. **Stage 1 — Regex Extraction:** extracts candidate information from the résumé text and produces an `ExtractedData` object.
2. **Stage 2 — FST Normalization:** converts recognized qualification variants and aliases into canonical names, preserving unrecognized terms.
3. **Canonical Ordering by Profile:** removes duplicate canonical qualifications, filters qualifications according to the selected profile, and sorts them deterministically.
4. **Stage 3 — Automata Recognition:** uses the generic automaton and the selected profile configuration to determine whether the ordered qualification sequence is accepted.
5. **Stage 4 — Grammar:** processes the structure according to the grammar defined for the system.

Each stage has a separate responsibility and communicates with the others through defined data structures.

Stage 1 does not normalize or classify qualifications. Stage 2 does not filter by profile. Canonical ordering does not implement the recognition automaton.
## 3. Input and Output

### Input

The ordering function receives three parameters:

- `normalized`: `NormalizedQualifications` object produced by Stage 2.
- `profile`: identifier of the profile selected by the user in the frontend.
- `catalog`: validated instance of `Catalog`, which contains qualifications, categories, positions, and associated profiles.

The profiles supported by the catalog are:

- `FULL_STACK`
- `ML_ENGINEER`
- `DEVOPS`
- `DATA_ENGINEER`

The profile is not fixed within the function nor is it automatically selected. The value provided by the interface is used and validated before processing the qualifications.

### Output

The function returns a list of canonical names (`list[str]`) that satisfies the following properties:

- Contains only qualifications recognized by the catalog.
- Includes only technologies enabled for the selected profile.
- Contains no canonical duplicates.
- Respects a deterministic order of categories and technologies.
- Does not include terms that Stage 2 marked as unrecognized.

Unrecognized terms remain in `normalized.unrecognized`. The ordering does not remove them from the original object nor does it modify the received information.

## 4. Function Interface

The interface defined for this stage is:

```python
def order(
    normalized: NormalizedQualifications,
    profile: str,
    catalog: Catalog,
) -> list[str]:
    ...
```

The function belongs to the `core.ordering` module.

A `Catalog` instance is received as a parameter to avoid coupling the ordering to a specific catalog loading implementation and to facilitate unit testing.

## 5. How Ordering Works

Processing follows a defined sequence of steps.

### 5.1. Profile Validation

The profile received from the frontend is validated against the profiles supported by the catalog.

If the profile does not exist, a custom exception `OrderingError` is raised, with a message that clearly identifies the problem.

This validation prevents a misspelled or unsupported profile from generating seemingly valid results.

### 5.2. Validation of Canonical Qualifications

Each received qualification must correspond to an existing canonical name in the catalog.

If an non-existent qualification appears, `OrderingError` is raised with an explicit message identifying the qualification that was not found.

Inconsistent data is not silently discarded, as this would make it difficult to detect errors between pipeline stages.

### 5.3. Duplicate Elimination

Repeated canonical qualifications are consolidated into a single occurrence.

For example, an input such as:

```python
["PYTHON", "KUBERNETES", "PYTHON", "DOCKER"]
```

is processed without keeping the repetitions of `PYTHON`.

Duplicate elimination occurs at this stage, not in Stage 2. The normalizer keeps repeated occurrences because its responsibility is to recognize and normalize candidates, not to organize them.

### 5.4. Profile Filtering

The catalog defines the profiles associated with each qualification.

The ordering keeps only the technologies that belong to the profile selected by the user.

For example, `REACT` is associated with `FULL_STACK`, while `DOCKER` and `KUBERNETES` are associated with `DEVOPS`.

A technology can belong to several profiles. In those cases, it is kept for each profile authorized by the catalog.

### 5.5. Profile-Specific Category Order

The category order is defined by the selected profile through `profile.canonical_order`. There is no single global category sequence shared by all profiles. Each profile declares the categories that are relevant to its qualification pattern and the order in which they must appear.

The configured orders are:

| Profile | Canonical order |
|---|---|
| Full Stack Developer | `LANGUAGE → FRONTEND → BACKEND → DATABASE → VCS` |
| Machine Learning Engineer | `LANGUAGE → ML_LIBRARY → DATABASE → VCS` |
| DevOps Engineer | `LANGUAGE → CONTAINER → CI_CD → IAC → CLOUD → VCS` |
| Data Engineer | `LANGUAGE → DATABASE → DATA_PROCESSING → WORKFLOW → CLOUD → VCS` |

During ordering, categories that are not included in the selected profile's `canonical_order` are excluded. This keeps the result aligned with the selected profile rather than applying categories that belong to other profiles.

### 5.6. Order Within Each Category

Technologies belonging to the same category are sorted using `Catalog.position()`.

The ordering stage therefore combines two criteria:

1. The category priority specified by the selected profile's `canonical_order`.
2. The qualification's position in the catalog, which acts as a tie-breaker within a category.

The final sequence is deterministic and does not depend on the order in which the candidate listed the skills.

## 6. Integration with the Catalog

The stage reuses the following operations from `Catalog`:

| Method or Property | Responsibility |
|---|---|
| `catalog.get(canonical)` | Retrieve the information of a canonical qualification. |
| `catalog.category_of(canonical)` | Query the category of a qualification. |
| `catalog.position(canonical)` | Obtain the position of a qualification to sort within its category. |
| `catalog.qualifications_for(profile, category)` | Query the qualifications associated with a profile and a category, in the order of the file. |
| `catalog.categories` | Query the categories in the order of first appearance in the JSON. |

The category priority comes from the selected profile's `canonical_order`, while `Catalog.position()` determines the order of qualifications within each category.

The profile information added to the catalog allows filtering technologies without duplicating eligibility rules in the ordering module.

## 7. Separation of Responsibilities

The architecture keeps normalization and profile organization separate.

**Stage 2 — Normalization:**

- Normalizes the extracted candidates.
- Recognizes variants and aliases using the FST.
- Produces canonical names.
- Keeps unrecognized terms.
- Does not filter by profile.
- Does not remove duplicates or sort qualifications.

**Canonical Ordering by Profile:**

- Validates the requested profile.
- Checks that qualifications are canonical and exist in the catalog.
- Removes duplicates.
- Filters technologies according to the profile.
- Sorts categories and qualifications.
- Keeps the input object intact.

This separation facilitates testing, reduces coupling between modules, and allows modifying ordering criteria without changing how the FST works.

## 8. Error Handling

A custom exception `OrderingError` is used to communicate errors specific to this stage.

Two main cases are addressed:

- **Invalid profile:** the profile sent from the frontend is not defined in the catalog.
- **Non-existent canonical qualification:** a received qualification does not correspond to any canonical name in the catalog.

The messages must identify the type of error and provide the problematic value when applicable.

The function must not convert these errors into an empty list, as that would hide inconsistencies in the data or in the integration between components.

## 9. Testing Strategy

Unit tests for this stage verify the following scenarios:

- Empty input and input with a single qualification.
- Filtering of technologies not allowed for the profile.
- Technologies shared among multiple profiles.
- Profiles with no matching qualifications.
- Profile-specific category order.
- Order by position within each category.
- Independence of the result from the initial input order.
- Elimination of canonical duplicates.
- Exclusion of unrecognized terms from the sorted result.
- Custom errors for invalid profiles and non-existent qualifications.
- Absence of modifications on the `NormalizedQualifications` object.
- Order stability in the face of changes in the layout of JSON categories.

The stage must also be tested integrated with Stage 2, verifying that the canonical qualifications produced by the FST are compatible with the input contract of the ordering stage.

## 10. Design Decisions

The main design decisions adopted are:

1. Keep normalization independent of the professional profile.
2. Use the catalog as the source of truth for qualifications, their categories, and their profiles.
3. Receive the profile selected by the user from the frontend, without establishing a default profile.
4. Eliminate canonical duplicates during ordering, not during normalization.
5. Use the category order declared by the selected profile through `profile.canonical_order`.
6. Use the catalog position to sort technologies within each category.
7. Use custom and explicit errors to detect invalid profiles and non-existent qualifications.
8. Preserve the original input and unrecognized terms.
9. Keep ordering as an independent module from the extraction, normalization, and recognition stages.

## 11. Expected Result

The stage delivers a list of canonical qualifications that is unique, filtered by profile, and ordered deterministically.

This output establishes a clear contract for the next phase of ResumeLens, which will be able to work with a consistent technology sequence specific to the requested profile.

The implementation of ordering does not replace or modify the FST of Stage 2, and it does not implement the recognition using automata of Stage 3. Each stage maintains its own responsibility within the pipeline.

---

## 12. Canonical Category Order and Profile Examples


| Profile | Canonical order |
|---|---|
| Full Stack Developer | `LANGUAGE → FRONTEND → BACKEND → DATABASE → VCS` |
| Machine Learning Engineer | `LANGUAGE → ML_LIBRARY → DATABASE → VCS` |
| DevOps Engineer | `LANGUAGE → CONTAINER → CI_CD → IAC → CLOUD → VCS` |
| Data Engineer | `LANGUAGE → DATABASE → DATA_PROCESSING → WORKFLOW → CLOUD → VCS` |

Team convention: `LANGUAGE` first and `VCS` always last.

#### Qualifications by profile and category

**Full Stack Developer**
- `LANGUAGE`: JAVASCRIPT, TYPESCRIPT, JAVA, PYTHON
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

The catalog query `qualifications_for(profile, category)` returns each group `G_i` in file order. The ordering stage uses this same query to filter qualifications before applying the profile's category order.

#### Examples

| Profile       | Input                                                      | Sorted Output                                             |
|---------------|------------------------------------------------------------|-----------------------------------------------------------|
| Full Stack    | `Git, NodeJS, JS, Postgres, React.js`                      | `JAVASCRIPT, REACT, NODE_JS, POSTGRESQL, GIT`             |
| ML Engineer   | `Git, PostgreSQL, TensorFlow, Pandas, Python`              | `PYTHON, PANDAS, TENSORFLOW, POSTGRESQL, GIT`             |
| DevOps        | `Terraform, Git, Docker, AWS, Python, Jenkins, Kubernetes` | `PYTHON, DOCKER, KUBERNETES, JENKINS, TERRAFORM, AWS, GIT` |
| Data Engineer | `Airflow, Git, Spark, PostgreSQL, Python, AWS`             | `PYTHON, POSTGRESQL, SPARK, AIRFLOW, AWS, GIT`            |

---
