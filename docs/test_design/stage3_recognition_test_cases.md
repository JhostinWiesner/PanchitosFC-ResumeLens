# Stage 3 Recognition — Test Cases

| ID | Scenario | Input | Expected Result |
| -- | -------- | ----- | --------------- |
| TC-01 | DFA structure for Full Stack | Build the DFA for FULL_STACK (LANGUAGE, FRONTEND, BACKEND, DATABASE, VCS) | 6 states (q0 to q5), initial state q0, only final state q5, deterministic |
| TC-02 | Groups match the documentation | Groups derived from the catalog for FULL_STACK | Same groups G1 to G5 as in the Stage 3 document |
| TC-03 | Assignment example, Full Stack | FULL_STACK: JAVASCRIPT, REACT, NODE_JS, POSTGRESQL, GIT | ACCEPTED |
| TC-04 | Assignment example, ML Engineer | ML_ENGINEER: PYTHON, PANDAS, TENSORFLOW, POSTGRESQL, GIT | ACCEPTED |
| TC-05 | Other alternatives in each group | FULL_STACK: TYPESCRIPT, ANGULAR, DJANGO, MONGODB, GIT | ACCEPTED |
| TC-06 | Several symbols from the same group | FULL_STACK: JAVASCRIPT, TYPESCRIPT, REACT, NODE_JS, SQL, POSTGRESQL, GIT | ACCEPTED |
| TC-07 | DevOps minimal profile | DEVOPS: PYTHON, DOCKER, GITHUB_ACTIONS, TERRAFORM, AWS, GIT | ACCEPTED |
| TC-08 | Data Engineer minimal profile | DATA_ENGINEER: PYTHON, POSTGRESQL, SPARK, AIRFLOW, AWS, GIT | ACCEPTED |
| TC-09 | One symbol per category, all profiles | For each profile: one qualification from each category (generated from the catalog) | ACCEPTED |
| TC-10 | Missing one category, all profiles | For each profile and each category: the sequence of TC-09 without that category (generated) | REJECTED |
| TC-11 | Missing version control | FULL_STACK: JAVASCRIPT, REACT, NODE_JS, POSTGRESQL | REJECTED (ends in q4, not a final state) |
| TC-12 | Missing language | FULL_STACK: REACT, NODE_JS, SQL, GIT | REJECTED (no transition from q0) |
| TC-13 | Only the first group | FULL_STACK: JAVASCRIPT | REJECTED (ends in q1) |
| TC-14 | Only the last group | FULL_STACK: GIT | REJECTED (no transition from q0) |
| TC-15 | Empty sequence | FULL_STACK: (empty) | REJECTED |
| TC-16 | Unordered input (outside the contract) | FULL_STACK: GIT, JAVASCRIPT, REACT, NODE_JS, POSTGRESQL | REJECTED, even though all requirements are present; shows that recognition depends on ordering |
| TC-17 | Unfiltered foreign symbol (outside the contract) | FULL_STACK: DOCKER, JAVASCRIPT, REACT, NODE_JS, SQL, GIT | REJECTED (no transition from q0); shows that recognition depends on filtering |
| TC-18 | Empty group | Build the DFA for FULL_STACK with categories LANGUAGE, ML_LIBRARY | ValueError mentioning category ML_LIBRARY |