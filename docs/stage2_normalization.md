# Normalization process

## Canonical names configuration

Catalog shared by the 4 profiles. It is read by Stage 1 (extraction), Stage 2 (normalization), and each `Profile`, ensuring the pipeline remains free of profile-specific logic.

All technologies recognized by ResumeLens live in `core/catalog.json`. Each entry has a canonical name (`UPPERCASE_WITH_UNDERSCORES`), a category, and a list of aliases. `core/catalog.py` only loads and validates the file; transforming text into canonical names is the job of the Stage 2 transducer. To add a qualification, edit the JSON only. The order of entries inside a category is the tie-breaker when ordering. Loading fails with a clear error if a canonical name is repeated or if two qualifications share the same spelling.

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