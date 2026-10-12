from core.catalog import Catalog
from core.extraction import extract
from core.normalization import normalize
from pipeline import run
from profiles.data_engineer import DATA_ENGINEER


def _data_engineer_evaluation(result):
    return next(
        evaluation
        for evaluation in result.candidate.evaluations
        if evaluation.profile_name == DATA_ENGINEER.name
    )


def test_extract_and_normalize_known_skills():
    catalog = Catalog.from_json()
    resume_text = """
    Jane Doe
    jane.doe@example.com

    Skills: Python, Docker, Git
    """

    extracted = extract(resume_text)
    normalized = normalize(extracted, catalog)

    assert extracted.skills_raw == ["Python", "Docker", "Git"]
    assert normalized.tokens == ["PYTHON", "DOCKER", "GIT"]
    assert normalized.unrecognized == []


def test_extract_and_normalize_preserves_unknown_terms():
    catalog = Catalog.from_json()
    unknown_skill = "tecnologia_inventada_xyz"

    resume_text = f"""
    Jane Doe
    jane.doe@example.com

    Skills: Python, {unknown_skill}, Docker
    """

    extracted = extract(resume_text)
    normalized = normalize(extracted, catalog)

    assert extracted.skills_raw == [
        "Python",
        unknown_skill,
        "Docker",
    ]
    assert normalized.tokens == ["PYTHON", "DOCKER"]
    assert normalized.unrecognized == [unknown_skill]


def test_extract_and_normalize_without_skills_section():
    catalog = Catalog.from_json()
    resume_text = """
    Jane Doe
    jane.doe@example.com

    Software developer with experience in backend development.
    """

    extracted = extract(resume_text)
    normalized = normalize(extracted, catalog)

    assert extracted.skills_raw == []
    assert normalized.tokens == []
    assert normalized.unrecognized == []


def test_extract_and_normalize_multiple_skills():
    catalog = Catalog.from_json()
    resume_text = """
    Jane Doe

    Technical Skills: JavaScript, Python, PostgreSQL
    """

    extracted = extract(resume_text)
    normalized = normalize(extracted, catalog)

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


def test_pipeline_accepts_data_engineer_skills_in_input_order():
    catalog = Catalog.from_json()
    resume_text = """Alex Morgan
alex@example.com

Technical Skills: Git, AWS, Airflow, Spark, PostgreSQL, Python
"""

    result = run(resume_text, DATA_ENGINEER, catalog)
    evaluation = _data_engineer_evaluation(result)

    assert result.extracted.skills_raw == [
        "Git", "AWS", "Airflow", "Spark", "PostgreSQL", "Python"
    ]
    assert result.normalized.tokens == [
        "GIT", "AWS", "AIRFLOW", "SPARK", "POSTGRESQL", "PYTHON"
    ]
    assert result.ordered.profile_name == DATA_ENGINEER.name
    assert result.ordered.sequence == [
        "PYTHON", "POSTGRESQL", "SPARK", "AIRFLOW", "AWS", "GIT"
    ]
    assert result.classification.profile_name == DATA_ENGINEER.name
    assert result.classification.accepted is True
    assert result.candidate.skills == result.ordered.sequence
    assert evaluation.accepted is True
    assert result.dsl_text
    assert result.html_output


def test_pipeline_rejects_data_engineer_resume_missing_required_category():
    catalog = Catalog.from_json()
    resume_text = """Jane Doe

Technical Skills: Python, PostgreSQL, Spark, AWS, Git
"""

    result = run(resume_text, DATA_ENGINEER, catalog)
    evaluation = _data_engineer_evaluation(result)

    assert "Airflow" not in result.extracted.skills_raw
    assert "AIRFLOW" not in result.normalized.tokens
    assert "AIRFLOW" not in result.ordered.sequence
    assert result.ordered.sequence == [
        "PYTHON", "POSTGRESQL", "SPARK", "AWS", "GIT"
    ]
    assert result.classification.accepted is False
    assert evaluation.accepted is False
    assert "\n    result: REJECTED\n" in result.dsl_text
    assert "REJECTED" in result.html_output


def test_pipeline_propagates_unknown_skill_and_deduplicates_ordered_skills():
    catalog = Catalog.from_json()
    unknown_skill = "SkillInventadaXYZ"
    resume_text = f"""Jane Doe

Technical Skills: Python, python, PostgreSQL, Spark, Airflow, AWS, Git, {unknown_skill}
"""

    result = run(resume_text, DATA_ENGINEER, catalog)

    assert result.extracted.skills_raw == [
        "Python", "python", "PostgreSQL", "Spark",
        "Airflow", "AWS", "Git", unknown_skill,
    ]
    assert result.normalized.tokens == [
        "PYTHON", "PYTHON", "POSTGRESQL", "SPARK", "AIRFLOW", "AWS", "GIT"
    ]
    assert result.normalized.unrecognized == [unknown_skill]
    assert result.ordered.sequence == [
        "PYTHON", "POSTGRESQL", "SPARK", "AIRFLOW", "AWS", "GIT"
    ]
    assert result.candidate.skills == result.ordered.sequence
    assert result.classification.accepted is True


def test_pipeline_serializes_and_renders_special_characters():
    catalog = Catalog.from_json()
    summary = 'Builds "trusted" pipelines & <data>.'
    resume_text = f"""José Núñez
jose.nunez@example.com

Professional Summary: {summary}
Technical Skills: Python, PostgreSQL, Spark, Airflow, AWS, Git
"""

    result = run(resume_text, DATA_ENGINEER, catalog)
    evaluation = _data_engineer_evaluation(result)

    assert result.extracted.name == "José Núñez"
    assert result.extracted.summary == summary
    assert result.candidate.summary == summary
    assert evaluation.accepted is True
    assert r'summary: "Builds \"trusted\" pipelines & <data>."' in result.dsl_text
    assert "José Núñez" in result.html_output
    assert "Builds &quot;trusted&quot; pipelines &amp; &lt;data&gt;." in result.html_output
    assert "ACCEPTED" in result.html_output
