
from core.extraction import extract
from core.normalization import normalize


def test_extract_and_normalize_known_skills():
    resume_text = """
    Jane Doe
    jane.doe@example.com

    Skills: Python, Docker, Git
    """

    extracted = extract(resume_text)
    normalized = normalize(extracted)

    assert extracted.skills_raw == ["Python", "Docker", "Git"]
    assert normalized.tokens == ["PYTHON", "DOCKER", "GIT"]
    assert normalized.unrecognized == []


def test_extract_and_normalize_preserves_unknown_terms():
    unknown_skill = "tecnologia_inventada_xyz"

    resume_text = f"""
    Jane Doe
    jane.doe@example.com

    Skills: Python, {unknown_skill}, Docker
    """

    extracted = extract(resume_text)
    normalized = normalize(extracted)

    assert extracted.skills_raw == [
        "Python",
        unknown_skill,
        "Docker",
    ]
    assert normalized.tokens == ["PYTHON", "DOCKER"]
    assert normalized.unrecognized == [unknown_skill]


def test_extract_and_normalize_without_skills_section():
    resume_text = """
    Jane Doe
    jane.doe@example.com

    Software developer with experience in backend development.
    """

    extracted = extract(resume_text)
    normalized = normalize(extracted)

    assert extracted.skills_raw == []
    assert normalized.tokens == []
    assert normalized.unrecognized == []


def test_extract_and_normalize_multiple_skills():
    resume_text = """
    Jane Doe

    Technical Skills: JavaScript, Python, PostgreSQL
    """

    extracted = extract(resume_text)
    normalized = normalize(extracted)

    assert extracted.skills_raw == [
        "JavaScript",
        "Python",
        "PostgreSQL",
    ]
    assert normalized.tokens == [
        "JAVASCRIPT",
        "PYTHON",
        "POSTGRESQL",
    ]
    assert normalized.unrecognized == []
