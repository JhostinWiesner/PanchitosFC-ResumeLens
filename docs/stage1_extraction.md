# Extraction Process

**Level 1 — Section Detection.** A resume does not have a fixed structure, so the first step is to locate the boundaries of each section (summary, skills, experience, education) within the full text. This is done by searching for lines that match one of the known headings (for example, “Skills,” “Technical Skills,” “Experience,” “Education,” or synonyms). Once a heading is located, all the text between that heading and the next one (or the end of the document) is considered the content of that section. This level does not extract data yet—it simply breaks the text down into smaller, more manageable blocks.

**Level 2 — Extraction of fields within each block.** Specific regular expressions tailored to each data type are applied to each isolated block (or to the entire text, in the case of contact information not tied to any section): one for email addresses, another for phone numbers, another to separate skills with commas, another to identify the duration of work experience, and so on. Each one recognizes a specific lexical pattern, not the document’s overall structure—that was already handled in Level 1.

This two-level separation is what allows the extractor to handle resumes with sections in different orders or with different section titles, without having to write a giant regex that attempts to capture the entire document at once.

---

## Definitions of Regular Expressions

This section documents the expressions that `core/extraction.py` actually executes. Each one is described in natural language and with the set notation used in the course: the regular operations **union** `∪`, **concatenation** `·` and **Kleene closure** `∗`, over an alphabet `Σ`, with `λ` as the empty string.

Every example below was checked against the implementation.

### Notation and conventions

| Symbol | Meaning |
|---|---|
| `Σ` | The alphabet: all Unicode characters |
| `λ` | The empty string; `{λ}` is the language that contains only it |
| `Xⁿ` | `X` concatenated with itself `n` times; `X⁺ = X · X∗` (one or more) |
| `X ∪ {λ}` | Python's `X?` (optional) |
| `X³ ∪ X⁴` | Python's `X{3,4}` (between three and four repetitions) |
| `⟨text⟩` | A literal written in lowercase whose letters may appear in either case, i.e. each letter `c` stands for `{c, C}`. Used where the expression is compiled with `re.IGNORECASE` / `(?i)` |

Character sets used throughout:

| Name | Definition |
|---|---|
| `D` | Decimal digits `{0, …, 9}` (Python's `\d` also admits other Unicode decimal digits) |
| `Word` | Letters, digits and `_` (Python's `\w`) |
| `Hsp` | Horizontal blanks `{space, tab}` |
| `WS` | All whitespace characters, including line breaks (Python's `\s`) |
| `X` | Any character except a line break (Python's `.`) |

**What "the language of an expression" means.** For an expression `r`, `L(r)` is the set of strings that `r` matches **in full**. When the code uses `search` to find a match inside a larger text, the strings it can find are those of `Σ∗ · L(r) · Σ∗`. The anchors `^` and `$`, look-arounds and capture groups are not part of the formal language: they are explained in natural language where they appear.

---

### 1. Section headings — `ANY_SECTION_HEADER`

```
(?im)^[ \t]*(?P<header>(?:(?:technical\s+skills|skills|technologies|tech\s+stack)|(?:professional\s+experience|work\s+experience|experience|employment)|(?:academic\s+background|academic\s+qualifications|education)))[ \t]*(?::[ \t]*(?P<inline>[^\r\n]*?)[ \t]*)?$
```

where the three alternatives are, with `\s+` between the words of multi-word headings:

```
skills:      technical\s+skills | skills | technologies | tech\s+stack
experience:  professional\s+experience | work\s+experience | experience | employment
education:   academic\s+background | academic\s+qualifications | education
```

**Natural language.** A line starts with a known section name, optionally indented and optionally followed by a colon and content on the same line. Inline content is recognized only after a colon. Case is ignored. The anchors (`^`, `$`, with `(?m)`) require the heading at the start of a line. Multi-word headings accept whitespace between words.

**Set notation.**

```
Sk = ⟨technical⟩·WS⁺·⟨skills⟩ ∪ ⟨skills⟩ ∪ ⟨technologies⟩ ∪ ⟨tech⟩·WS⁺·⟨stack⟩
Ex = ⟨professional⟩·WS⁺·⟨experience⟩ ∪ ⟨work⟩·WS⁺·⟨experience⟩ ∪ ⟨experience⟩ ∪ ⟨employment⟩
Ed = ⟨academic⟩·WS⁺·⟨background⟩ ∪ ⟨academic⟩·WS⁺·⟨qualifications⟩ ∪ ⟨education⟩

L(heading line) = Hsp∗ · (Sk ∪ Ex ∪ Ed) · Hsp∗ · ({λ} ∪ {:} · Hsp∗ · X∗) · Hsp∗
```

The type of a section is decided by `SECTION_HEADER_PATTERNS`, which applies `(?i)^(?:…)$` to the heading once the colon is removed: its three languages are exactly `Sk`, `Ex` and `Ed`. A section's content runs from the end of its heading to the start of the next recognized heading (or the end of the text).

| Accepted | Rejected |
|---|---|
| `Technical Skills:` | `Skills and tools` (extra words) |
| `  EXPERIENCE  ` | `My experience is broad` (heading inside a sentence) |
| `Skills: JS, Git` | `Skills and tools` (extra words) |

**Limitations.** Inline content must follow a colon. Since `\s+` also matches line breaks, a heading split across two lines (`Technical⏎Skills`) is accepted.

---

### 2. Candidate name — `NAME`

```
^[A-ZÀ-ÖØ-Þ][A-Za-zÀ-ÖØ-öø-ÿ'’.-]*(?:[ \t]+[A-ZÀ-ÖØ-Þ][A-Za-zÀ-ÖØ-öø-ÿ'’.-]*){1,3}$
```

**Natural language.** A line made of **two to four words** separated by blanks. Each word starts with an uppercase letter (accented capitals included) followed by any number of letters, apostrophes, dots or hyphens. The code applies it with `fullmatch` to one stripped line, and only to the first five lines before the first section heading, skipping lines that contain an email, phone, LinkedIn or GitHub address.

| Accepted | Rejected |
|---|---|
| `Wednesday Addams` | `Wednesday` (one word) |
| `Ana María O'Brien-Pérez` | `wednesday addams` (lowercase initial) |
| `Jean-Luc Picard` | `Ana de la Cruz` (lowercase particles) |

**Limitations.** Lowercase particles (`de`, `la`, `van`) break the pattern. Any capitalized two-to-four-word line has the same form, so `Technical Skills` would also match; that is why the search is restricted to the header area.

---

### 3. Email — `EMAIL`

```
[A-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Z0-9](?:[A-Z0-9-]*[A-Z0-9])?(?:\.[A-Z0-9](?:[A-Z0-9-]*[A-Z0-9])?)+     (re.IGNORECASE)
```

**Natural language.** A local part of one or more allowed characters (letters, digits and the symbols `. ! # $ % & ' * + / = ? ^ _ ` { | } ~ -`), an `@`, and a domain of **two or more labels** separated by dots. Each label starts and ends with a letter or digit and may contain hyphens in between. The code takes the first match found in the text.

**Set notation.**

```
A    = {a, …, z} ∪ {A, …, Z} ∪ {0, …, 9}
Loc  = A ∪ {., !, #, $, %, &, ', *, +, /, =, ?, ^, _, `, {, |, }, ~, -}
Lab  = A · ((A ∪ {-})∗ · A ∪ {λ})
          (a label: starts and ends with an alphanumeric character)

L(EMAIL) = Loc⁺ · {@} · Lab · ({.} · Lab)⁺
```

| Accepted | Rejected |
|---|---|
| `ana.ruiz@mail.co` | `ana@localhost` (domain has one label) |
| `a+b@sub.example.org` | `ana@-bad.com` (label starts with a hyphen) |
| `a@b.co.uk` | `@x.com` (empty local part) |

**Limitations.** It is a simplified version of the full email grammar: it does not check lengths, quoted local parts or international domain names. It accepts a one-letter last label (`ana@x.c`). Accented characters are not in `Loc`.

---

### 4. Phone number — `PHONE`

```
(?<!\w)(?:\+?\d{1,3}[ .()-]?)?(?:\(?\d{2,4}\)?[ .-]?)\d{3,4}[ .-]?\d{3,4}(?!\w)
```

**Natural language.** An optional country code (an optional `+`, one to three digits and an optional separator), then an area code (two to four digits, optionally in parentheses, with an optional separator), then two blocks of three or four digits optionally separated by a blank, dot or hyphen. The look-arounds `(?<!\w)` and `(?!\w)` require that the number is **not glued to a letter or digit** on either side. A candidate is then accepted by `_find_phone` only if it has 7 to 15 digits and is not a year range.

**Set notation.**

```
S1 = {space, ., (, ), -}          S2 = {space, ., -}

CC   = ({+} ∪ {λ}) · (D ∪ D² ∪ D³) · (S1 ∪ {λ})            (country code)
AREA = ({(} ∪ {λ}) · (D² ∪ D³ ∪ D⁴) · ({)} ∪ {λ}) · (S2 ∪ {λ})
BLK  = D³ ∪ D⁴

L(PHONE) = (CC ∪ {λ}) · AREA · BLK · (S2 ∪ {λ}) · BLK
           with the context condition: the match is neither preceded nor followed by a character of Word
```

With these limits, the shortest string has 8 digits and the longest has 15.

| Accepted | Rejected |
|---|---|
| `+57 300 123 4567` | `555-1234` (too few digits) |
| `(604) 555-1234` | `2021-2023` (a year range, not a number) |
| `3001234567` | `ref12345678901` (glued to letters) |

**Limitations.** It does not validate that a country or area code exists, so any digit sequence with the right shape is a candidate.

---

### 5. LinkedIn profile — `LINKEDIN`

```
(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+     (re.IGNORECASE)
```

**Natural language.** An optional `http://` or `https://`, an optional `www.`, the fixed text `linkedin.com/in/`, and a username of one or more letters, digits, underscores or hyphens. Case is ignored. Trailing punctuation that is not part of the username is removed afterwards by the code.

**Set notation.**

```
H = {http://, https://} ∪ {λ}          W = {www.} ∪ {λ}          U = Word ∪ {-}

L(LINKEDIN) = H · W · ⟨linkedin.com/in/⟩ · U⁺
```

| Accepted | Rejected |
|---|---|
| `linkedin.com/in/ana-ruiz` | `linkedin.com/in/` (empty username) |
| `HTTPS://www.LinkedIn.com/in/x_1` | `linkedin.com/company/acme` (not a personal profile) |

---

### 6. GitHub profile — `GITHUB`

```
(?:https?://)?(?:www\.)?github\.com/[\w-]+     (re.IGNORECASE)
```

**Natural language.** Same structure as the LinkedIn expression, but with the fixed text `github.com/` followed by a username of letters, digits, underscores or hyphens.

**Set notation.**

```
L(GITHUB) = H · W · ⟨github.com/⟩ · U⁺          (H, W and U as in section 5)
```

| Accepted | Rejected |
|---|---|
| `github.com/ana-ruiz` | `github.com/` (empty username) |
| `https://github.com/anaruiz` | `gitlab.com/ana` (different site) |

**Limitations.** For a repository URL such as `github.com/anaruiz/project`, the match stops at the username, so only `github.com/anaruiz` is kept.

---

### 7. Labeled location — `LOCATION_LABELED`

```
(?im)^[ \t]*(?:location|based[ \t]+in|address)[ \t]*:[ \t]*(.+?)[ \t]*$
```

**Natural language.** A line that starts with the label `Location`, `Based in` or `Address`, followed by a colon and a **non-empty value** up to the end of the line. Case is ignored. The capture group holds the value, trimmed of trailing blanks (the non-greedy `.+?` followed by `[ \t]*$` is what trims them). It is searched in the whole text.

**Set notation.**

```
Lab = ⟨location⟩ ∪ ⟨based⟩ · Hsp⁺ · ⟨in⟩ ∪ ⟨address⟩

L(line) = Hsp∗ · Lab · Hsp∗ · {:} · Hsp∗ · X⁺ · Hsp∗
```

| Accepted | Rejected |
|---|---|
| `Location: Cali, Colombia` | `Location Cali` (no colon) |
| `Based in : Medellín` | `Location:` (empty value) |
| `BASED   IN: Lima` | `City: Cali` (label not recognized) |

---

### 8. Unlabeled location — `LOCATION_INLINE`

```
^[ \t]*([A-ZÀ-ÖØ-Þ][A-Za-zÀ-ÖØ-öø-ÿ.'’ -]*?)\s*,\s*([A-ZÀ-ÖØ-Þ][A-Za-zÀ-ÖØ-öø-ÿ.'’ -]*?)[ \t]*$
```

**Natural language.** A line made of **two capitalized places separated by a comma**, such as a city and a country. Each place starts with an uppercase letter and continues with letters, dots, apostrophes, hyphens or spaces. The code applies it with `fullmatch` to each stripped line, and **only in the header area** (before the first section heading), and only when no labeled location was found.

| Accepted | Rejected |
|---|---|
| `Cali, Colombia` | `cali, colombia` (lowercase initials) |
| `San José, Costa Rica` | `Cali` (no comma) |
| `Bogotá, D.C.` | `Cali, Colombia, South America` (three parts) |

**Limitations.** The pattern cannot tell a place from any other capitalized pair: `Python, Java` also matches. That is why it is restricted to the header area and never run over the skills or education sections.

---

### 9. Skills separator — `SKILL_DELIMITER`

```
[,;\n]+
```

**Natural language.** One or more consecutive commas, semicolons or line breaks. It only marks where one skill ends and the next begins; it does not recognize the content of a skill. Deciding that `JS` and `Javascript` are the same technology is the job of the transducer in Stage 2.

**Set notation.**

```
Sep = {',', ';', '\n'}

L(SKILL_DELIMITER) = Sep⁺
```

The code uses it with `split`, so the pieces between delimiters become the raw tokens of `skills_raw`, trimmed of boundary punctuation.

| Accepted | Rejected |
|---|---|
| `,` | the empty string (needs at least one separator) |
| `;⏎,` | `, ` (the space is not a separator; it stays in the token and is trimmed afterwards) |

---

### 10. Experience period — `PERIOD`

```
(?i)(?<!\d)(?:19|20)\d{2}[ \t]*(?:[-–—]|\bto\b)[ \t]*(?:(?:19|20)\d{2}|present\b|current\b)(?!\w)
```

**Natural language.** A four-digit year between 1900 and 2099, then a hyphen, en dash, em dash or the word `to` (with optional blanks around it), then either another year in the same range or the word `present` or `current`. Case is ignored. The look-arounds require that the range is not glued to another digit before it or to a letter or digit after it. Its matches are the anchors the extractor uses to split the experience section into entries.

**Set notation.**

```
Y   = ({1}·{9} ∪ {2}·{0}) · D · D                      (years 1900–2099)
Dash = {-, –, —} ∪ ⟨to⟩
End  = Y ∪ ⟨present⟩ ∪ ⟨current⟩

L(PERIOD) = Y · Hsp∗ · Dash · Hsp∗ · End
            with the context condition: not preceded by a digit and not followed by a character of Word
```

| Accepted | Rejected |
|---|---|
| `2021-2023` | `2021` (a single year) |
| `2019 – Present` | `2021 Present` (needs a dash or `to`) |
| `2020 to current` | `Jan 2021 - Mar 2023` (months are not supported) |
| `2021 - PRESENT` | `12021-2023` (preceded by a digit) |

**Limitations.** Month-and-year ranges are not recognized. Years outside 1900–2099 do not match.

---

### 11. Organization and period line — `ORG_PERIOD_LINE`

```
^[ \t]*(?P<organization>[^|·]+?)[ \t]*[|·][ \t]*(?P<period>.+?)[ \t]*$
```

**Natural language.** A line with the form `Organization | something` or `Organization · something`. The first group is the organization: one or more characters that are neither `|` nor `·`. Then comes the separator `|` or `·`, and the second group is any non-empty text. The code applies it with `fullmatch` to one stripped line. It does not check that the second part is a date; `PERIOD` is used for that.

**Set notation.**

```
Org = Σ ∖ {|, ·}                    (every character except the two separators)
Sp  = {|, ·}

L(ORG_PERIOD_LINE) = Hsp∗ · Org⁺ · Hsp∗ · Sp · Hsp∗ · X⁺ · Hsp∗
```

| Accepted | Rejected |
|---|---|
| `Acme Corp \| 2021-2023` | `Acme Corp 2021-2023` (no separator) |
| `Globant · 2019 – Present` | `\| 2021` (empty organization) |
| `A \| B \| 2020` | `Acme Corp \|` (nothing after the separator) |

**Limitations.** Since the organization cannot contain a separator, only the first one splits the line. In `A | B | 2020`, the organization is `A` and the period group is `B | 2020`.

---

### 12. Experience bullet — `BULLET_LINE`

```
^[ \t]*[•●▪*\-][ \t]+(.+?)[ \t]*$
```

**Natural language.** A line that starts with a bullet marker (`•`, `●`, `▪`, `*` or `-`), at least one blank, and then the text of the bullet up to the end of the line. The capture group is the text without the marker and without trailing blanks, and it is kept as written, without rewriting. The code uses it with `fullmatch` on each stripped line of an experience entry.

**Set notation.**

```
M = {•, ●, ▪, *, -}

L(BULLET_LINE) = Hsp∗ · M · Hsp⁺ · X⁺ · Hsp∗
```

| Accepted | Rejected |
|---|---|
| `- Built REST APIs` | `-Built` (no blank after the marker) |
| `  • Led a team` | `Built - REST` (does not start with a marker) |
| `* Used Docker` | `- ` (no text after the marker) |

**Limitations.** Other markers, such as the en dash `–`, are not recognized. A line that starts with `- ` and a number (for example `- 5% increase`) is treated as a bullet.

---

## Contract with Stage 2

This section defines what Stage 1 (`extract`) requires from its input and what it guarantees in `ExtractedData`. Stage 2 and later stages may rely on these guarantees and nothing else.

### Input

- `resume_text` is plain text (UTF-8). PDF and DOCX files are out of scope.
- `extract` removes a leading BOM and converts `\r\n` and `\r` to `\n` as its first step, before applying any expression.
- The résumé is semi-structured: each section is introduced by a recognized header (see the header list above). A header may appear alone on its line (`Technical Skills:`) or followed by content on the same line (`Technical Skills: JS, React.js`). Both layouts appear in the assignment examples.
- Content outside a recognized section is never searched for qualifications.

### Output: `ExtractedData`

| Field | Guarantee | When not found |
|---|---|---|
| `name` | First matching line among the first five lines before the first section header; contact lines are skipped | `""` |
| `contact` | Email and location have edge punctuation trimmed; phone is returned as matched; LinkedIn and GitHub have trailing punctuation removed | The field is `None` (never an empty string) |
| `summary` | Non-contact lines after the detected name and before the first recognized header; line edges are trimmed and repeated blank lines are collapsed | `""` if no name is found or no summary text remains |
| `skills_raw` | Tokens from the skills section (see below) | `[]` |
| `education` | One entry per non-empty line of the education section, list markers removed, literal text | `[]` |
| `experience` | Entries are grouped around recognized date-range lines; if no dated entries can be formed, non-empty blank-line-separated blocks are used. Order is preserved; bullet markers are removed | `[]`. Inside an entry, `organization` and `period` are `""` if not found |

Stage 1 never raises an error because of missing information: absence is always represented by an empty value.

### Guarantees on each token of `skills_raw`

1. The token is not empty.
2. It has no leading or trailing whitespace.
3. Supported leading list markers (`-`, `*`, `•`) and configured edge punctuation are removed. Internal punctuation is preserved, including in `Node.js`, `C++` and `C#`.
4. Upper and lower case are preserved exactly as written.
5. Tokens appear in the order of the résumé, and repeated tokens are kept.
6. Tokens are separated only at commas, semicolons, and line breaks.

### Reference examples (used as contract tests)

1. Header and content on the same line:
   `Technical Skills: JS, React.js, NodeJS, Postgres, Git.` gives `["JS", "React.js", "NodeJS", "Postgres", "Git"]`.
2. Header alone on its line, content on the following line: same result.
3. Résumé without a skills header: `skills_raw == []`, no error.
4. Input with `\r\n` line endings: same result as with `\n`.

