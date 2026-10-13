# Stage 4 — Candidate Profile Grammar

## Purpose and flow

Stage 4 represents the information extracted from a résumé, its normalized
skills, and the qualification evaluation as a candidate-profile document. The
document is written in a small domain-specific language (DSL) defined in
[`core/grammar/candidate.tx`](../core/grammar/candidate.tx).

The stage follows this flow:

1. `build_candidate_profile` combines `ExtractedData`,
   `OrderedQualifications`, `ClassificationResult`, and the selected `Profile`
   into a `CandidateProfile`.
2. `to_dsl` serializes that candidate profile into text in the candidate
   language. Empty optional parts are omitted.
3. `parse_candidate` validates the DSL with a textX metamodel created from
   `candidate.tx`. TextX errors are exposed as `CandidateSyntaxError`.
4. `render_html` receives the validated model and builds a self-contained HTML
   candidate profile.

The pipeline performs these operations in
[`pipeline.py`](../pipeline.py): it builds the candidate, serializes it,
validates the serialization, and renders the validated model.

## Complete valid example

The following document is the `BASE_DSL` assignment example used by
`test_full_valid_profile` in
[`tests/test_grammar.py`](../tests/test_grammar.py):

```text
candidate
    name: "Wednesday Addams"
end

contact
    email: wednesday.addams@example.com
    location: "Nevermore Academy, Jericho"
end

summary: "Detail-oriented developer with three years of experience developing web applications."

experience
    title: "Web Application Developer"
    organization: "Nevermore Academy Projects"
    period: "3 years"
    bullet: "Developed web applications for organizing investigation notes."
    bullet: "Implemented backend services using Node.js."
end

education: "B.Sc. in Computer Science"

skills: JAVASCRIPT, REACT, NODE_JS, POSTGRESQL, GIT

evaluation
    profile: "Full Stack Developer"
    result: ACCEPTED
    explanation: "The normalized qualifications satisfy an accepted Full Stack Developer pattern."
end
```

## Grammar

### EBNF

The following EBNF is a notation-oriented transcription of
[`candidate.tx`](../core/grammar/candidate.tx). `STRING`, `Email`, and
`SkillName` are lexical terminals; `Result` is a grammar rule whose alternatives
are literal terminals. Whitespace between tokens is accepted by the textX
parser, as demonstrated by the layout test.

```ebnf
CandidateProfile = Personal,
                   [ Contact ],
                   [ "summary", ":", STRING ],
                   { Experience },
                   { Education },
                   [ "skills", ":", SkillName, { ",", SkillName } ],
                   Evaluation, { Evaluation } ;

Personal         = "candidate", "name", ":", STRING, "end" ;

Contact          = "contact",
                   [ "email", ":", Email ],
                   [ "phone", ":", STRING ],
                   [ "location", ":", STRING ],
                   [ "linkedin", ":", STRING ],
                   [ "github", ":", STRING ],
                   "end" ;

Experience       = "experience",
                   "title", ":", STRING,
                   [ "organization", ":", STRING ],
                   [ "period", ":", STRING ],
                   { "bullet", ":", STRING },
                   "end" ;

Education        = "education", ":", STRING ;

Evaluation       = "evaluation",
                   "profile", ":", STRING,
                   "result", ":", Result,
                   "explanation", ":", STRING,
                   "end" ;

Result           = "ACCEPTED" | "REJECTED" ;
```

### Terminals

| Terminal | Definition |
|---|---|
| Keywords | `candidate`, `name`, `end`, `contact`, `email`, `phone`, `location`, `linkedin`, `github`, `summary`, `experience`, `title`, `organization`, `period`, `bullet`, `education`, `skills`, `evaluation`, `profile`, `result`, and `explanation` |
| Punctuation | `:` separates labels from values; `,` separates skills |
| `STRING` | A textX string literal. It is used for free text such as names, summaries, titles, locations, periods, bullets, education text, profile names, and explanations. |
| `Email` | `/[^\s@]+@[^\s@]+\.[^\s@]+/` |
| `SkillName` | `/[A-Z0-9]+(_[A-Z0-9]+)*/` |
| `Result` | The literal `ACCEPTED` or the literal `REJECTED` |

The `Email` pattern requires non-whitespace, non-`@` text before the `@`, a
non-empty domain component before a dot, and at least one dot-separated suffix.
The `SkillName` pattern accepts uppercase letters or digits, with optional
additional uppercase-or-digit components separated by underscores.

### Non-terminals

| Non-terminal | Meaning |
|---|---|
| `CandidateProfile` | Complete document: one personal block, optional contact and summary, zero or more experiences and education records, optional skills, and one or more evaluations |
| `Personal` | Required candidate block containing the candidate name |
| `Contact` | Optional contact block with optional email, phone, location, LinkedIn, and GitHub fields |
| `Experience` | Experience block with a required title, optional organization and period, and zero or more bullets |
| `Education` | One education record |
| `Evaluation` | Evaluation block containing profile, result, and explanation |
| `Result` | Accepted or rejected evaluation result |

## Structural characteristics

### Section order

The top-level order is fixed:

1. `Personal`
2. optional `Contact`
3. optional `summary`
4. zero or more `Experience` blocks
5. zero or more `Education` records
6. optional `skills`
7. one or more `Evaluation` blocks

For example, the tests reject a document that moves `skills` before an
`experience` block.

### Repetition and optional parts

The `Personal` block and at least one `Evaluation` are required. Contact,
summary, skills, organization, period, and all contact fields are optional.
Experiences, education records, bullets, and evaluations are repeatable.
`test_repeated_elements` accepts two experiences, two education records, and
two evaluations. `test_optional_parts_omitted` and
`test_empty_parts_are_omitted` verify the optional cases.

### Block structure

`Personal`, `Contact`, `Experience`, and `Evaluation` are delimited by their
opening keyword and a closing `end`. Their labels occur in a fixed order
inside each block. `Education` and `skills` are single-line constructs rather
than `end`-delimited blocks.

### Two kinds of values

The grammar has two value classes:

- Quoted free text uses textX `STRING`. The serializer escapes double quotes,
  and the tests verify that escaped quotes, multiline summaries, and non-ASCII
  names and locations survive a serialization/parsing round trip.
- Typed terminals constrain specific values. Emails use `Email`, skills use
  uppercase `SkillName` values separated by commas, and results use the
  `ACCEPTED` or `REJECTED` alternatives.

### Unambiguity

The grammar uses distinct section keywords and labels, fixed field order, and
different lexical forms for its typed values. Consequently, a valid token
sequence identifies one structural interpretation: a block keyword selects
the block type, each label selects its field, and `Result` has only two
possible literal values. The tests exercise this structure through successful
parses, rejected reordered documents, and round trips.

## Validation

`parse_candidate` accepts a document only when it matches the textX metamodel.
It returns the parsed model on success and converts `TextXError` into
`CandidateSyntaxError` on failure.

The tests verify rejection of the following examples:

- a document without the required `candidate` block;
- a document without an `evaluation` block;
- sections in the wrong order;
- an experience without its required `end`;
- an unterminated quoted string;
- a malformed email such as `not-an-email`;
- lowercase skills such as `javascript, react`;
- an invalid result such as `PENDING`;
- an unknown section such as `hobbies: "chess"`;
- skills without comma separators, such as `JAVASCRIPT REACT`;
- an experience without its required `title`;
- empty or whitespace-only input.

The tests also verify successful parsing of every canonical catalog name as a
`SkillName`, both accepted and rejected evaluation results, repeated elements,
optional parts, and emails such as `a@b.co` and
`first.last+tag@mail.example.com`.

## HTML visualization

`render_html` is called with the model returned by `parse_candidate`; the
pipeline does not render the pre-validation DSL. It generates a self-contained
HTML page containing personal information, optional summary, experience,
education, normalized skills, and qualification evaluations.

Every value interpolated into the HTML is passed through
`html.escape(..., quote=True)`, including the candidate name, contact fields,
summary, experience fields and bullets, education text, skills, evaluation
profile, result, and explanation.

## Limitations

- The grammar requires the top-level sections to appear in the order defined
  by `CandidateProfile`; it is not a general unordered document format.
- A candidate must have a `candidate` block and at least one `evaluation`.
- `Contact`, `summary`, `skills`, and several fields inside blocks are optional,
  but the grammar does not provide defaults for missing required fields.
- Skills must use canonical-style uppercase names matching `SkillName`; aliases
  and lowercase spellings are not accepted directly by this grammar.
- The `Email` terminal checks lexical shape only. It does not verify that an
  address exists or is deliverable.
- The grammar validates the DSL structure and lexical forms. It does not itself
  determine whether the qualifications satisfy a profile; that result is
  supplied by the recognition stage and serialized as `ACCEPTED` or `REJECTED`.
