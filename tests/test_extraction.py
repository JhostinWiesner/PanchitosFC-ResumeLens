import pytest

from core.extraction import extract
from core.types import ContactInfo, ExperienceEntry, ExtractedData


SAMPLE_RESUME = """Wednesday Addams
Wednesday@example.com | +1 212-555-0198
linkedin.com/in/wednesday-addams | github.com/waddams
New York, USA
Curious software developer with a passion for solving problems.

TECHNICAL SKILLS:
Python, React.js; Node.js, PostgreSQL,
Git, .NET, scikit-learn.

EXPERIENCE:
Software Developer
Nevermore Labs · 2021 – Present
- Built web applications.
* Improved API performance.

EDUCATION:
- BSc Computer Science, Nevermore University
MSc Software Engineering, Nightshade Institute
"""


def test_extract_returns_pipeline_contract():
    result = extract(SAMPLE_RESUME)
    assert isinstance(result, ExtractedData)
    assert isinstance(result.contact, ContactInfo)
    assert result.experience and isinstance(result.experience[0], ExperienceEntry)


def test_extracts_name_and_contact_without_edge_punctuation():
    result = extract(SAMPLE_RESUME)
    assert result.name == "Wednesday Addams"
    assert result.contact.email == "Wednesday@example.com"
    assert result.contact.phone == "+1 212-555-0198"
    assert result.contact.location == "New York, USA"
    assert result.contact.linkedin == "linkedin.com/in/wednesday-addams"
    assert result.contact.github == "github.com/waddams"


def test_summary_excludes_name_contact_and_unlabeled_location():
    result = extract(SAMPLE_RESUME)
    assert result.summary == "Curious software developer with a passion for solving problems."


def test_skills_are_raw_and_boundary_punctuation_is_cleaned():
    result = extract(SAMPLE_RESUME)
    assert result.skills_raw == ["Python", "React.js", "Node.js", "PostgreSQL", "Git", ".NET", "scikit-learn"]


def test_extracts_education_lines_and_preserves_internal_commas():
    result = extract(SAMPLE_RESUME)
    assert result.education == [
        "BSc Computer Science, Nevermore University",
        "MSc Software Engineering, Nightshade Institute",
    ]


def test_extracts_experience_and_bullets():
    result = extract(SAMPLE_RESUME)
    assert len(result.experience) == 1
    entry = result.experience[0]
    assert entry.title == "Software Developer"
    assert entry.organization == "Nevermore Labs"
    assert entry.period == "2021 – Present"
    assert entry.bullets == ["Built web applications.", "Improved API performance."]


def test_multiple_experiences_do_not_require_blank_line_between_entries():
    text = """Jane Doe
EXPERIENCE
Software Engineer
Acme Corp | 2021-2023
- Developed backend services
- Improved performance
Data Analyst
Example Inc | 2023-PRESENT
- Analyzed datasets"""
    result = extract(text)
    assert result.experience == [
        ExperienceEntry("Software Engineer", "Acme Corp", "2021-2023", ["Developed backend services", "Improved performance"]),
        ExperienceEntry("Data Analyst", "Example Inc", "2023-PRESENT", ["Analyzed datasets"]),
    ]



def test_experience_supports_title_organization_and_period_on_separate_lines():
    result = extract("""Jane Doe
EXPERIENCE
Software Engineer
Acme Corp
2021-2023
- Built services""")
    assert result.experience == [
        ExperienceEntry("Software Engineer", "Acme Corp", "2021-2023", ["Built services"])
    ]

def test_skills_are_not_misclassified_as_location_when_contact_is_missing():
    result = extract("Jane Doe\nSKILLS\nPython, Java")
    assert result.contact.location is None
    assert result.skills_raw == ["Python", "Java"]
    assert result.summary == ""


def test_labeled_location_is_detected_in_contact_header():
    result = extract("Jane Doe\nLocation: Cali, Colombia\nSKILLS\nPython")
    assert result.contact.location == "Cali, Colombia"
    assert result.skills_raw == ["Python"]


def test_missing_sections_return_empty_collections():
    result = extract("Mary Jane Watson\nmary@example.com")
    assert result.name == "Mary Jane Watson"
    assert result.skills_raw == []
    assert result.education == []
    assert result.experience == []


def test_section_order_and_aliases_are_supported():
    result = extract("""Jane Doe
Education:
- Systems Engineering
Work Experience:
Developer
Acme | 2020-2022
- Wrote code
Tech Stack:
Python; Java""")
    assert result.education == ["Systems Engineering"]
    assert result.skills_raw == ["Python", "Java"]
    assert result.experience[0].organization == "Acme"


def test_crlf_line_endings_are_supported():
    result = extract("Jane Doe\r\nSKILLS:\r\nPython, Java\r\nEDUCATION:\r\n- Systems Engineering")
    assert result.skills_raw == ["Python", "Java"]
    assert result.education == ["Systems Engineering"]


def test_date_range_is_not_extracted_as_phone():
    result = extract("Jane Doe\nEXPERIENCE\nDeveloper\nAcme | 2021-2023")
    assert result.contact.phone is None


def test_non_string_input_is_rejected():
    with pytest.raises(TypeError):
        extract(None)
