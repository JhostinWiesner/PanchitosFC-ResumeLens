from dataclasses import replace

import pytest

from core.catalog import Catalog
from core.grammar.grammar import (
    CandidateSyntaxError,
    build_candidate_profile,
    parse_candidate,
    to_dsl,
)
from core.types import (
    CandidateProfile,
    ClassificationResult,
    ContactInfo,
    Evaluation,
    ExperienceEntry,
    ExtractedData,
    NormalizedQualifications,
)
from profiles.base import Profile


BASE_DSL = """candidate
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
"""


@pytest.fixture(scope="session")
def catalog() -> Catalog:
    return Catalog.from_json()


def make_wednesday_candidate(accepted: bool = True) -> CandidateProfile:
    return CandidateProfile(
        name="Wednesday Addams",
        contact=ContactInfo(email="wednesday.addams@example.com"),
        summary="",
        experience=[
            ExperienceEntry(
                title="Web Application Developer",
                organization="Nevermore Academy Projects",
                period="3 years",
                bullets=[
                    "Developed web applications for organizing investigation notes.",
                    "Implemented backend services using Node.js.",
                ],
            )
        ],
        education=[],
        skills=["JAVASCRIPT", "REACT", "NODE_JS", "POSTGRESQL", "GIT"],
        evaluations=[
            Evaluation(
                profile_name="Full Stack Developer",
                accepted=accepted,
                explanation=(
                    "The normalized qualifications satisfy an accepted "
                    "Full Stack Developer pattern."
                ),
            )
        ],
    )


def test_minimal_valid_profile():
    """TC-G01: A candidate and evaluation form a minimal valid profile."""
    model = parse_candidate(
        'candidate\n    name: "Wednesday Addams"\nend\n'
        '\nevaluation\n'
        '    profile: "Full Stack Developer"\n'
        "    result: ACCEPTED\n"
        '    explanation: "Accepted."\n'
        "end\n"
    )

    assert model.personal.full_name == "Wednesday Addams", "The candidate name was not parsed"


def test_full_valid_profile():
    """TC-G02: The assignment example parses with all key values."""
    model = parse_candidate(BASE_DSL)

    assert model.personal.full_name == "Wednesday Addams", "Unexpected candidate name"
    assert model.contact.email == "wednesday.addams@example.com", "Unexpected email"
    assert len(model.experiences) == 1, "Expected one experience"
    assert len(model.experiences[0].bullets) == 2, "Expected two experience bullets"
    assert model.skills == [
        "JAVASCRIPT",
        "REACT",
        "NODE_JS",
        "POSTGRESQL",
        "GIT",
    ], "Unexpected skills"
    assert model.evaluations[0].result == "ACCEPTED", "Expected an accepted evaluation"


def test_repeated_elements():
    """TC-G03: Repeated experiences, educations, and evaluations are accepted."""
    dsl = """candidate
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

experience
    title: "Data Engineer"
    organization: "Nevermore Academy"
    period: "1 year"
end

education: "B.Sc. in Computer Science"
education: "M.Sc. in Computer Science"

skills: JAVASCRIPT, REACT, NODE_JS, POSTGRESQL, GIT

evaluation
    profile: "Full Stack Developer"
    result: ACCEPTED
    explanation: "The normalized qualifications satisfy an accepted Full Stack Developer pattern."
end

evaluation
    profile: "ML Engineer"
    result: REJECTED
    explanation: "Not accepted."
end
"""

    model = parse_candidate(dsl)

    assert len(model.experiences) == 2, "Expected two experiences"
    assert len(model.educations) == 2, "Expected two education records"
    assert len(model.evaluations) == 2, "Expected two evaluations"


def test_optional_parts_omitted():
    """TC-G04: Optional contact fields and profile sections may be omitted."""
    dsl = (
        'candidate\n    name: "Wednesday Addams"\nend\n\n'
        "contact\n    email: wednesday.addams@example.com\nend\n\n"
        'experience\n    title: "Developer"\nend\n\n'
        'evaluation\n    profile: "Full Stack Developer"\n'
        "    result: ACCEPTED\n    explanation: \"Accepted.\"\nend\n"
    )
    model = parse_candidate(dsl)

    assert model.contact.email == "wednesday.addams@example.com", "Email was not parsed"
    assert not model.contact.phone, "Omitted phone should be empty"
    assert not model.experiences[0].organization, "Omitted organization should be empty"
    assert not model.experiences[0].period, "Omitted period should be empty"
    assert not model.summary, "Omitted summary should be empty"
    assert model.educations == [], "Omitted education should be empty"
    assert model.skills == [], "Omitted skills should be empty"


def test_layout_does_not_matter():
    """TC-G05: Indentation and blank-line layout do not change parsed values."""
    dsl = BASE_DSL.replace(
        'candidate\n    name: "Wednesday Addams"\nend',
        'candidate\n  name: "Wednesday Addams"\n\n  end',
    )
    model = parse_candidate(dsl)

    assert model.personal.full_name == "Wednesday Addams", "Name changed with layout"
    assert model.contact.email == "wednesday.addams@example.com", "Email changed with layout"
    assert len(model.experiences[0].bullets) == 2, "Bullets changed with layout"


def test_escaped_quote_in_free_text():
    """TC-G06: Escaped quotes in free text are accepted."""
    dsl = BASE_DSL.replace(
        "Developed web applications for organizing investigation notes.",
        'Developed web applications for organizing \\"Case Files\\".',
    )

    model = parse_candidate(dsl)

    assert model.experiences[0].bullets[0] == (
        'Developed web applications for organizing "Case Files".'
    ), "Escaped quote was not decoded"


@pytest.mark.parametrize(
    "dsl",
    [
        BASE_DSL.replace(
            'candidate\n    name: "Wednesday Addams"\nend\n\n',
            "",
        ),
        BASE_DSL[: BASE_DSL.index("\nevaluation\n")],
        BASE_DSL.replace(
            "skills: JAVASCRIPT, REACT, NODE_JS, POSTGRESQL, GIT\n\n",
            "",
            1,
        ).replace(
            "\nexperience\n",
            "\nskills: JAVASCRIPT, REACT, NODE_JS, POSTGRESQL, GIT\n\nexperience\n",
            1,
        ),
        BASE_DSL.replace("\nend\n\neducation:", "\n\neducation:", 1),
        BASE_DSL.replace('name: "Wednesday Addams"', 'name: "Wednesday Addams', 1),
        BASE_DSL.replace("wednesday.addams@example.com", "not-an-email", 1),
        BASE_DSL.replace(
            "skills: JAVASCRIPT, REACT, NODE_JS, POSTGRESQL, GIT",
            "skills: javascript, react",
            1,
        ),
        BASE_DSL.replace("result: ACCEPTED", "result: PENDING", 1),
        BASE_DSL.replace(
            'summary: "Detail-oriented developer with three years of experience '
            'developing web applications."\n\n',
            'summary: "Detail-oriented developer with three years of experience '
            'developing web applications."\n\nhobbies: "chess"\n\n',
            1,
        ),
        BASE_DSL.replace(
            "skills: JAVASCRIPT, REACT, NODE_JS, POSTGRESQL, GIT",
            "skills: JAVASCRIPT REACT",
            1,
        ),
        BASE_DSL.replace('    title: "Web Application Developer"\n', "", 1),
    ],
    ids=[
        "TC-G07",
        "TC-G08",
        "TC-G09",
        "TC-G10",
        "TC-G11",
        "TC-G12",
        "TC-G13",
        "TC-G14",
        "TC-G15",
        "TC-G16",
        "TC-G17",
    ],
)
def test_invalid_documents_are_rejected(dsl):
    """TC-G07, TC-G08, TC-G09, TC-G10, TC-G11, TC-G12, TC-G13, TC-G14, TC-G15, TC-G16, TC-G17: Each malformed document is rejected."""
    assert dsl != BASE_DSL, "The invalid test document must differ from BASE_DSL"
    with pytest.raises(CandidateSyntaxError):
        parse_candidate(dsl)


@pytest.mark.parametrize(
    "text",
    ["", "   \n  "],
    ids=["TC-G18-empty", "TC-G18-spaces"],
)
def test_empty_document_is_rejected(text):
    """TC-G18: an empty or whitespace-only document is rejected."""
    with pytest.raises(CandidateSyntaxError):
        parse_candidate(text)



def test_round_trip():
    """TC-G19: A Wednesday Addams candidate survives DSL serialization and parsing."""
    candidate = make_wednesday_candidate()
    model = parse_candidate(to_dsl(candidate))

    assert model.personal.full_name == candidate.name, "Name changed during round trip"
    assert model.contact.email == candidate.contact.email, "Email changed during round trip"
    assert model.experiences[0].bullets == candidate.experience[0].bullets, (
        "Bullets changed during round trip"
    )
    assert model.skills == candidate.skills, "Skills changed during round trip"
    assert model.evaluations[0].result == "ACCEPTED", "Result changed during round trip"


def test_empty_parts_are_omitted():
    """TC-G20: Empty optional candidate parts are omitted from the DSL."""
    candidate = CandidateProfile(
        name="Wednesday Addams",
        contact=ContactInfo(),
        summary="",
        experience=[],
        education=[],
        skills=[],
        evaluations=[
            Evaluation("Full Stack Developer", True, "Accepted.")
        ],
    )
    dsl = to_dsl(candidate)
    model = parse_candidate(dsl)

    assert not any(line.startswith("contact") for line in dsl.splitlines()), (
        "Empty contact block should be omitted"
    )
    assert not any(line.startswith("summary") for line in dsl.splitlines()), (
        "Empty summary should be omitted"
    )
    assert not any(line.startswith("education") for line in dsl.splitlines()), (
        "Empty education should be omitted"
    )
    assert not any(line.startswith("skills") for line in dsl.splitlines()), (
        "Empty skills should be omitted"
    )
    assert model.personal.full_name == candidate.name, "Candidate should remain valid"


def test_rejected_result():
    """TC-G21: A rejected evaluation is serialized as REJECTED and parses."""
    dsl = to_dsl(make_wednesday_candidate(accepted=False))

    assert "result: REJECTED" in dsl, "Rejected result was not serialized"
    parse_candidate(dsl)


def test_quote_in_free_text_survives():
    """TC-G22: A double quote in free text survives the round trip."""
    candidate = make_wednesday_candidate()
    candidate = replace(
        candidate,
        experience=[
            ExperienceEntry(
                title=candidate.experience[0].title,
                organization=candidate.experience[0].organization,
                period=candidate.experience[0].period,
                bullets=['Investigated "Case Files".', candidate.experience[0].bullets[1]],
            )
        ],
    )

    model = parse_candidate(to_dsl(candidate))

    assert model.experiences[0].bullets[0] == candidate.experience[0].bullets[0], (
        "The escaped quote did not survive the round trip"
    )


def test_every_catalog_name_is_a_valid_skill(catalog):
    """TC-G23: Every canonical catalog name is accepted as a skill."""
    skills = ", ".join(qualification.canonical for qualification in catalog)
    dsl = BASE_DSL.replace(
        "skills: JAVASCRIPT, REACT, NODE_JS, POSTGRESQL, GIT",
        f"skills: {skills}",
        1,
    )

    model = parse_candidate(dsl)

    assert model.skills == [qualification.canonical for qualification in catalog], (
        "The catalog skill list was not parsed in order"
    )


@pytest.mark.parametrize(
    "accepted",
    [True, False],
    ids=["TC-G24-accepted", "TC-G24-rejected"],
)
def test_building_candidate_profile(accepted):
    """TC-G24: Building a candidate preserves extracted data and evaluation details."""
    profile = Profile("FULL_STACK", "Full Stack Developer", ("LANGUAGE",))
    extracted = ExtractedData(
        name="Wednesday Addams",
        contact=ContactInfo(email="wednesday.addams@example.com"),
        summary="Detail-oriented developer.",
        skills_raw=[],
        education=["B.Sc. in Computer Science"],
        experience=[
            ExperienceEntry(
                title="Web Application Developer",
                organization="Nevermore Academy Projects",
                period="3 years",
                bullets=["Developed web applications."],
            )
        ],
    )
    normalized = NormalizedQualifications(
        tokens=["JAVASCRIPT", "REACT", "JAVASCRIPT", "GIT"],
        unrecognized=[],
    )
    classification = ClassificationResult(profile.name, accepted)

    candidate = build_candidate_profile(extracted, normalized, classification, profile)

    assert candidate.name == extracted.name, "Candidate name was not preserved"
    assert candidate.contact == extracted.contact, "Contact information was not preserved"
    assert candidate.summary == extracted.summary, "Summary was not preserved"
    assert candidate.education == extracted.education, "Education was not preserved"
    assert candidate.experience == extracted.experience, "Experience was not preserved"
    assert candidate.skills == ["JAVASCRIPT", "REACT", "GIT"], (
        "Skills were not deduplicated in first-seen order"
    )
    assert len(candidate.evaluations) == 1, "Expected one evaluation"
    assert candidate.evaluations[0].profile_name == profile.name, (
        "Evaluation profile name is incorrect"
    )
    assert candidate.evaluations[0].accepted is accepted, "Evaluation result is incorrect"
    assert candidate.evaluations[0].explanation == profile.get_explanation(accepted), (
        "Profile explanation was not obtained from the profile"
    )


def test_multiline_free_text():
    """TC-G28: Multi-line summary text survives the DSL round trip."""
    candidate = replace(
        make_wednesday_candidate(),
        summary="First line.\nSecond line.",
    )
    model = parse_candidate(to_dsl(candidate))

    assert model.summary == candidate.summary, "Multi-line summary changed during round trip"


def test_non_ascii_characters():
    """TC-G29: Non-ASCII names and locations survive the DSL round trip."""
    candidate = replace(
        make_wednesday_candidate(),
        name="José Núñez",
        contact=ContactInfo(
            email="jose.nunez@example.com",
            location="Bogotá, Colombia",
        ),
    )
    model = parse_candidate(to_dsl(candidate))

    assert model.personal.full_name == candidate.name, "Non-ASCII name changed"
    assert model.contact.location == candidate.contact.location, (
        "Non-ASCII location changed"
    )


@pytest.mark.parametrize(
    "email",
    ["a@b.co", "first.last+tag@mail.example.com"],
    ids=["TC-G31-short", "TC-G31-plus"],
)
def test_email_forms(email):
    """TC-G30: Supported email forms survive the DSL round trip."""
    candidate = replace(
        make_wednesday_candidate(),
        contact=ContactInfo(email=email),
    )
    model = parse_candidate(to_dsl(candidate))

    assert model.contact.email == email, "Email changed during round trip"