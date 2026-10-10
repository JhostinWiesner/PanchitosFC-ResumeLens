# ResumeLens — Canonical Ordering by Profile

## 1. General Description

The canonical ordering by profile stage is responsible for organizing the technical qualifications extracted from a resume, taking into account the professional profile selected by the user from the frontend.

This stage receives the qualifications that have already been normalized by the system, removes duplicates, filters out technologies that do not correspond to the selected profile, and organizes the result using a deterministic order of categories and technologies.

The goal is to deliver a consistent list of canonical qualifications that can be used by the subsequent stages of the ResumeLens pipeline.

## 2. Location within the Pipeline

The processing flow is organized as follows:

1. **Stage 1 — Extraction:** obtains information from the resume and extracts technical qualification candidates.
2. **Stage 2 — Normalization:** uses a finite-state transducer (FST) to convert recognized variants and aliases into canonical names.
3. **Canonical Ordering by Profile:** removes duplicates, filters qualifications according to the chosen profile, and organizes technologies by category.
4. **Stage 3 — Recognition:** uses automata to recognize sequences of qualifications corresponding to the profile.
5. **Stage 4 — Grammar:** processes the recognized structure using the grammar defined for the system.

Ordering is an independent responsibility from normalization. Stage 2 recognizes technologies without depending on the selected profile, while this stage determines which ones are kept for subsequent processing.

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

### 5.5. Fixed Category Order

The order of categories is explicitly defined in the ordering stage. It does not depend on the position of the categories in the JSON file.

The established order is:

1. `LANGUAGE`
2. `FRONTEND`
3. `BACKEND`
4. `DATABASE`
5. `ML_LIBRARY`
6. `DATA_PROCESSING`
7. `WORKFLOW`
8. `CONTAINER`
9. `CI_CD`
10. `IAC`
11. `CLOUD`
12. `VCS`

This decision allows the result to remain stable even if the catalog file is reorganized later.

### 5.6. Order Within Each Category

Technologies belonging to the same category are sorted using `Catalog.position()`.

This function returns the global position of the qualification in the JSON and allows preserving the relative order defined for the technologies in the catalog.

Thus, the ordering combines two criteria:

- Fixed category priority.
- Position of the qualification within the catalog.

## 6. Integration with the Catalog

The stage reuses the following operations from `Catalog`:

| Method or Property | Responsibility |
|---|---|
| `catalog.get(canonical)` | Retrieve the information of a canonical qualification. |
| `catalog.category_of(canonical)` | Query the category of a qualification. |
| `catalog.position(canonical)` | Obtain the position of a qualification to sort within its category. |
| `catalog.qualifications_for(profile, category)` | Query the qualifications associated with a profile and a category, in the order of the file. |
| `catalog.categories` | Query the categories in the order of first appearance in the JSON. |

Although the catalog provides these operations, the fixed priority of categories belongs to the ordering stage and remains independent of the JSON order.

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
- Fixed category order.
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
5. Define a fixed category order independent of the JSON.
6. Use the catalog position to sort technologies within each category.
7. Use custom and explicit errors to detect invalid profiles and non-existent qualifications.
8. Preserve the original input and unrecognized terms.
9. Keep ordering as an independent module from the extraction, normalization, and recognition stages.

## 11. Expected Result

The stage delivers a list of canonical qualifications that is unique, filtered by profile, and ordered deterministically.

This output establishes a clear contract for the next phase of ResumeLens, which will be able to work with a consistent technology sequence specific to the requested profile.

The implementation of ordering does not replace or modify the FST of Stage 2, and it does not implement the recognition using automata of Stage 3. Each stage maintains its own responsibility within the pipeline.