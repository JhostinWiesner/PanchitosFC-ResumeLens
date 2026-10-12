# Stage 2 — Normalization and Ordering Test Cases

## 1. Normalization Test Cases

| ID | Scenario | Input | Expected Result |
|---|---|---|---|
| TC-N01 | All catalog spellings | All spellings returned by `catalog.spellings()` | Returns a `NormalizedQualifications` instance. All spellings are mapped to their canonical names, and `unrecognized` is empty. |
| TC-N02 | Aliases and variants | `JS`, `React.JS`, `Scikit-Learn`, `Google Cloud Platform`, `K8s` | Tokens are `JAVASCRIPT`, `REACT`, `SCIKIT_LEARN`, `GCP`, `KUBERNETES`, in that order. `unrecognized` is empty. |
| TC-N03 | Unknown candidates are preserved | `Rust`, `tecnologia_inventada`, `pythonx` | `tokens` is empty. All three inputs are preserved in `unrecognized`, in their original order. |
| TC-N04 | Mixed known and unknown candidates | `Python`, `Rust`, `PyTorch`, `UnknownTech` | `tokens` contains `PYTHON`, `PYTORCH`. `unrecognized` contains `Rust`, `UnknownTech`, in their original order. |
| TC-N05 | Duplicate candidates are preserved | `Python`, `PYTHON`, `py` | `tokens` contains three occurrences of `PYTHON`. `unrecognized` is empty. |
| TC-N06 | Blank candidates are ignored | Empty string, spaces, tab, `Python` | `tokens` contains only `PYTHON`. `unrecognized` is empty. |
| TC-N07 | Empty skills list | Empty list of skills | Both `tokens` and `unrecognized` are empty. |

## 2. Ordering Test Cases

| ID | Scenario | Input | Expected Result |
|---|---|---|---|
| TC-O01 | Ordered qualifications output | `GIT`, `AWS`, `DOCKER`, `PYTHON` for `DEVOPS` | Returns `OrderedQualifications` with profile name `DevOps Engineer` and sequence `PYTHON`, `DOCKER`, `AWS`, `GIT`. |
| TC-O02 | Filtering qualifications outside the profile | `REACT`, `PYTHON`, `DOCKER`, `GIT` for `DEVOPS` | `sequence` contains `PYTHON`, `DOCKER`, `GIT`. `REACT` is excluded. |
| TC-O03 | Duplicate qualifications are removed | `PYTHON`, `DOCKER`, `PYTHON`, `GIT`, `DOCKER` for `DEVOPS` | `sequence` contains `PYTHON`, `DOCKER`, `GIT`, with no duplicates. |
| TC-O04 | Profile category ordering | `GIT`, `AWS`, `TERRAFORM`, `JENKINS`, `KUBERNETES`, `BASH` for `DEVOPS` | `sequence` contains `BASH`, `KUBERNETES`, `JENKINS`, `TERRAFORM`, `AWS`, `GIT`, following the profile's category order. |
| TC-O05 | Empty qualifications | Empty `tokens` list for `DEVOPS` | `profile_name` is `DevOps Engineer` and `sequence` is empty. |
| TC-O06 | Input immutability | `GIT`, `PYTHON`, `DOCKER`, with `UnknownTool` in `unrecognized` | Calling `order()` does not modify the original `tokens` or `unrecognized` lists. |
| TC-O07 | Unrecognized terms are preserved | `PYTHON`, `DOCKER`, with `UnknownTool` in `unrecognized` | `sequence` contains `PYTHON`, `DOCKER`; `unrecognized` remains unchanged. |
| TC-O08 | Unknown canonical qualification | `NOT_A_REAL_QUALIFICATION` for `DEVOPS` | Raises `KeyError`. |

## 3. Scope and Expected Behavior

### Normalization

Normalization transforms recognized skill names and their variants into canonical names defined in the shared catalog. Unrecognized terms are retained in `unrecognized`. Duplicate recognized candidates are preserved at this stage, and blank candidates are ignored.

Normalization is global and does not depend on the selected professional profile.

### Ordering

Ordering filters the normalized qualifications according to the selected profile's eligible skills and category order. It removes duplicate qualifications and sorts the remaining skills according to the category priority defined by `canonical_order`, followed by the position of each qualification in the catalog.

The ordering stage does not modify the original normalized qualifications or the list of unrecognized terms.

The current Ordering test cases use the `DEVOPS` profile. They verify the ordering and filtering behavior for that profile.