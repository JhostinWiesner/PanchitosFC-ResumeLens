# Extraction Process

**Level 1 — Section Detection.** A resume does not have a fixed structure, so the first step is to locate the boundaries of each section (summary, skills, experience, education) within the full text. This is done by searching for lines that match one of the known headings (for example, “Skills,” “Technical Skills,” “Experience,” “Education,” or synonyms). Once a heading is located, all the text between that heading and the next one (or the end of the document) is considered the content of that section. This level does not extract data yet—it simply breaks the text down into smaller, more manageable blocks.

**Level 2 — Extraction of fields within each block.** Specific regular expressions tailored to each data type are applied to each isolated block (or to the entire text, in the case of contact information not tied to any section): one for email addresses, another for phone numbers, another to separate skills with commas, another to identify the duration of work experience, and so on. Each one recognizes a specific lexical pattern, not the document’s overall structure—that was already handled in Level 1.

This two-level separation is what allows the extractor to handle resumes with sections in different orders or with different section titles, without having to write a giant regex that attempts to capture the entire document at once.

---

## Definitions of Regular Expressions

### Level 1 — Section Heading

```
^(TECHNICAL SKILLS|SKILLS|TECHNOLOGIES|TECH STACK|EXPERIENCE|WORK EXPERIENCE|PROFESSIONAL EXPERIENCE|EMPLOYMENT|EDUCATION|ACADEMIC BACKGROUND|ACADEMIC QUALIFICATIONS):?$
```

(applied case-insensitively, and anchored to the beginning and end of the line)

**What it recognizes:** a complete line that is exactly one of the known section names, with an optional colon at the end. The `|` symbol indicates a choice between several possible words or phrases—that is, the line must match one (and only one) of those complete options, not just a part of it. The circumflex accent at the beginning and the dollar sign at the end ensure that the match covers the entire line, so as not to confuse, for example, the word “Experience” if it appears within a paragraph of free-form text.

---

### Candidate's Name

```
^[A-Z][a-z]+( [A-Z][a-z]+){1,3}$
```

**What it matches:** a line consisting of 2 to 4 words, each beginning with an uppercase letter from A to Z followed by one or more lowercase letters from a to z, separated by a single space. This applies only to the first lines of the document, before any section headers, because the same pattern of “words with an initial capital letter” also appears later in organization names.

---

### Email

```
[A-Za-z0-9.]+@[A-Za-z0-9]+\.[A-Za-z]{2,}
```

**What it recognizes:** a sequence of letters, digits, or dots, followed by the `@` symbol, followed by another sequence of letters or digits, followed by a dot, and ending with at least two letters. This is a simplified version of the official email regex, which is much more complex; it is sufficient for the purpose of extracting candidate emails from resumes.

---

### Phone number

```
[0-9]{2,4}[- ]?[0-9]{3,4}[- ]?[0-9]{3,4}
```

**What it recognizes:** groups of 2 to 4 digits, then 3 to 4 digits, then 3 to 4 digits, each group separated optionally by a space or a dash. This covers different regional formats of phone numbers without requiring one exact format, since the statement does not specify a single format.

---

### Location (LinkedIn/GitHub)

```
LINKEDIN.COM/IN/[A-Za-z0-9-]+
```

**What it recognizes:** the literal text "linkedin.com/in/" (regardless of case) followed by one or more letters, digits, or hyphens, which corresponds to the username.

---

### Skills separator (within the skills section already isolated at Level 1)

```
[,;\n]+
```

**What it recognizes:** one or more consecutive characters that are a comma, semicolon, or newline. It does not recognize the content of each skill in itself — it only marks where one item ends and the next begins. This is intentional: it is not the responsibility of this stage to decide if "JS" and "Javascript" are the same, as that is resolved by the transducer in the next stage.

---

### Experience period

```
[0-9]{4}[- ]+([0-9]{4}|PRESENT|CURRENT)
```

**What it recognizes:** a year of 4 digits, followed by a dash or space, followed by another year of 4 digits or the word "PRESENT" or "CURRENT" (without distinguishing between uppercase and lowercase). Covers formats like "2021-2023" or "2021 Present".

---

### Experience bullets

```
^[-*] [A-Za-z].+$
```

**What it recognizes:** a line that starts with a dash or an asterisk, followed by a space and then a letter, until the end of the line. The content that follows is captured as-is, without rewriting, according to what we agreed upon.


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
| `name` | First line of the document that matches the name pattern | `""` |
| `contact` | Each field holds the matched text, unmodified | The field is `None` (never an empty string) |
| `summary` | Literal text between the name and the first recognized header, without contact lines | `""` |
| `skills_raw` | Tokens from the skills section (see below) | `[]` |
| `education` | One entry per non-empty line of the education section, list markers removed, literal text | `[]` |
| `experience` | One entry per block, in order of appearance; `bullets` are literal text with the marker removed | `[]`. Inside an entry, `organization` and `period` are `""` if not found |

Stage 1 never raises an error because of missing information: absence is always represented by an empty value.

### Guarantees on each token of `skills_raw`

1. The token is not empty.
2. It has no leading or trailing whitespace.
3. It has no list marker (`-`, `*`, `•`) at the start and no sentence-final punctuation (`.`, `;`, `:`) at the end. Characters that can belong to a technology name (`.`, `+`, `#`, `-`) are preserved inside the token, so `Node.js`, `C++` and `C#` are not altered.
4. Upper and lower case are preserved exactly as written.
5. Tokens appear in the order of the résumé, and repeated tokens are kept.
6. Tokens are separated only at commas, semicolons, and line breaks.

### Reference examples (used as contract tests)

1. Header and content on the same line:
   `Technical Skills: JS, React.js, NodeJS, Postgres, Git.` gives `["JS", "React.js", "NodeJS", "Postgres", "Git"]`.
2. Header alone on its line, content on the following line: same result.
3. Résumé without a skills header: `skills_raw == []`, no error.
4. Input with `\r\n` line endings: same result as with `\n`.

