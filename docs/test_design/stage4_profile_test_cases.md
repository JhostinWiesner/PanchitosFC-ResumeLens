# Stage 4 — Test Cases

| ID | Scenario | Input | Expected Result |
| -- | -------- | ----- | --------------- |
| TC-G01 | Minimal valid profile | Only the `candidate` block and one `evaluation` block | Accepted; the name is the given one |
| TC-G02 | Full valid profile (assignment example) | BASE_DSL | Accepted; name, email, one experience with 2 bullets, the skills, and the result ACCEPTED are in the model |
| TC-G03 | Repeated elements | Two experiences, two education records, two evaluations | Accepted; the model has 2 experiences, 2 education records, and 2 evaluations |
| TC-G04 | Optional parts omitted | `contact` with only `email`; an experience without organization and period; no summary, education, or skills | Accepted; the omitted fields are empty |
| TC-G05 | Layout does not matter | BASE_DSL with different indentation and extra blank lines | Accepted; same values as TC-G02 |
| TC-G06 | Escaped quote in free text | A bullet that contains `\"Case Files\"` | Accepted |
| TC-G07 | Missing personal block | BASE_DSL without the `candidate` block | Rejected |
| TC-G08 | Missing evaluation | BASE_DSL cut right before `evaluation` | Rejected |
| TC-G09 | Sections out of order | BASE_DSL with the `skills` line moved before the `experience` block | Rejected |
| TC-G10 | Missing `end` | BASE_DSL without the `end` that closes the experience block | Rejected |
| TC-G11 | Unterminated string | BASE_DSL with the closing quote of the name removed | Rejected |
| TC-G12 | Malformed email | `email: not-an-email` | Rejected |
| TC-G13 | Skill in lowercase | `skills: javascript, react` | Rejected |
| TC-G14 | Invalid result | `result: PENDING` | Rejected |
| TC-G15 | Unknown section | A line `hobbies: "chess"` after the summary | Rejected |
| TC-G16 | Skills without commas | `skills: JAVASCRIPT REACT` | Rejected |
| TC-G17 | Experience without title | BASE_DSL without the `title` line | Rejected |
| TC-G18 | Empty text | An empty string, and a string with only spaces | Rejected |
| TC-G19 | Round trip | `to_dsl` of the Wednesday Addams candidate, then `parse_candidate` | Accepted; name, email, bullets, skills, and result equal the original |
| TC-G20 | Empty parts are omitted | A candidate without contact, summary, education, or skills | The text has no `contact`, `summary`, `education`, or `skills` lines, and it is accepted |
| TC-G21 | Rejected result | A candidate whose classification is not accepted | The text contains `result: REJECTED` and it is accepted |
| TC-G22 | Quote in free text survives | A bullet that contains a double quote | After the round trip the bullet equals the original |
| TC-G23 | Every catalog name is a valid skill | A `skills:` list with every canonical name of the catalog | Accepted |
| TC-G24 | Building the candidate profile | `build_candidate_profile` with repeated tokens and an accepted classification | Skills without repeats in order of first appearance; one evaluation with the profile name, the result, and the profile's explanation |
| TC-G25 | Multi-line free text | A candidate whose summary has two lines (a line break inside the text) | After the round trip the summary equals the original |
| TC-G26 | Non-ASCII characters | A candidate whose name and location contain accents and ñ (for example "José Núñez", "Bogotá, Colombia") | After the round trip the values equal the original |
| TC-G27 | Email forms | Emails such as `a@b.co` and `first.last+tag@mail.example.com` in the contact | Accepted, and the email is preserved |