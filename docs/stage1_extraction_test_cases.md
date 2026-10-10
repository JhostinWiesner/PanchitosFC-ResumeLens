# Stage 1 Extraction Test Cases

These cases document the scenarios implemented in `tests/test_extraction.py`. `SAMPLE_RESUME` refers to the fixture defined in that file.

| ID | Scenario | Input | Expected Result |
| -- | -------- | ----- | --------------- |
| EXT-01 | Output uses the pipeline data types | `SAMPLE_RESUME` | Result is `ExtractedData`; `contact` is `ContactInfo`; the first experience is an `ExperienceEntry`. |
| EXT-02 | Extract name and contact fields | `SAMPLE_RESUME` | Name is `Wednesday Addams`; email is `Wednesday@example.com`; phone is `+1 212-555-0198`; location is `New York, USA`; LinkedIn is `linkedin.com/in/wednesday-addams`; GitHub is `github.com/waddams`. |
| EXT-03 | Summary excludes contact details and location | `SAMPLE_RESUME` | Summary is `Curious software developer with a passion for solving problems.` |
| EXT-04 | Raw skills preserve punctuation, case, order, and duplicates | `SAMPLE_RESUME` | Skills are `Python`, `React.js`, `Node.js`, `PostgreSQL`, `Git`, `.NET`, `scikit-learn`, `C++`, `C#`, `Python`, `python`, in that order. |
| EXT-05 | Education lines retain internal commas | `SAMPLE_RESUME` with `• BSc,` appended to its education section | Education is `["BSc Computer Science, Nevermore University", "MSc Software Engineering, Nightshade Institute", "BSc,"]`; the list marker is removed. |
| EXT-06 | Extract one experience and its bullets | `SAMPLE_RESUME` | One entry: title `Software Developer`, organization `Nevermore Labs`, period `2021 – Present`, and bullets `Built web applications.`, `Improved API performance.`, and `Reduced errors!`. |
| EXT-07 | Group multiple experiences without blank separators | Two dated entries and bullets in one continuous experience section | Two ordered entries with their respective titles, organizations, periods, and bullets. |
| EXT-08 | Parse title, organization, and period on separate lines | `Jane Doe`, then `Software Engineer`, `Acme Corp`, `2021-2023`, and a bullet | One entry: `Software Engineer`, `Acme Corp`, `2021-2023`, bullet `Built services`. |
| EXT-09 | Do not infer location from skills | `Jane Doe\nSKILLS\nPython, Java` | Location is `None`; skills are `["Python", "Java"]`; summary is empty. |
| EXT-10 | Remove skill list markers | Skills section containing `- Python`, `* Java`, and `• Git` | Skills are `["Python", "Java", "Git"]`. |
| EXT-11 | Extract a labeled location | `Jane Doe\nLocation: Cali, Colombia\nSKILLS\nPython` | Location is `Cali, Colombia`; skills are `["Python"]`. |
| EXT-12 | Missing sections return empty collections | `Mary Jane Watson\nmary@example.com` | Name is `Mary Jane Watson`; email is `mary@example.com`; summary is empty; skills, education, and experience are empty lists. |
| EXT-13 | Remove a leading BOM | BOM followed by `Jane Doe\nSKILLS:\nPython` | Name is `Jane Doe`; skills are `["Python"]`; contact, summary, education, and experience have their empty values. |
| EXT-14 | Accept isolated and inline section headers | Two independent parameterized inputs: `Technical Skills:\nPython, Java` and `Technical Skills: Python, Java`; each is followed by an education header | Each of the two test invocations yields skills `["Python", "Java"]`, education `["BSc Computer Science"]`, no experience, and empty summary. |
| EXT-15 | Recognize section aliases and varied order | Education, Work Experience, and Tech Stack sections | Education contains `Systems Engineering`; skills are `["Python", "Java"]`; experience organization is `Acme`. |
| EXT-16 | Support CRLF line endings | Resume text with `\r\n` separators across contact, summary, skills, experience, and education | All fields match the asserted normalized values, including one experience entry. |
| EXT-17 | Support CR-only line endings | `Jane Doe\rSKILLS:\rPython` | Name is `Jane Doe`; skills are `["Python"]`. |
| EXT-18 | Bound summary by name and first section | Name, email, `Backend engineer.`, then Skills and Education sections | Summary is `Backend engineer.`; skills and education contain only their section content. |
| EXT-19 | Exclude text before the detected name from summary | Introductory text, `Jane Doe`, email, `Backend engineer`, then Skills | Name is `Jane Doe`; summary is `Backend engineer`. |
| EXT-20 | Preserve parentheses in phone number | `Jane Doe\n(604) 555-1234` | Phone is exactly `(604) 555-1234`. |
| EXT-21 | Empty text returns an empty result | Empty string | `ExtractedData(name="", contact=ContactInfo(email=None, phone=None, location=None, linkedin=None, github=None), summary="", skills_raw=[], education=[], experience=[])`. |
| EXT-22 | Do not extract a date range as a phone number | Experience with `Acme \| 2021-2023` | Phone is `None`. |
| EXT-23 | Reject non-string input | `None` | `extract` raises `TypeError`. |
