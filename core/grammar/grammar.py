from __future__ import annotations
import html
from pathlib import Path

from textx import metamodel_from_file
from textx.exceptions import TextXError



from core.types import (
    CandidateProfile,
    ClassificationResult,
    ContactInfo,
    ExperienceEntry,
    Evaluation,
    ExtractedData,
    NormalizedQualifications,
)
from profiles.base import Profile

class CandidateSyntaxError(ValueError):
    """The text does not follow the candidate profile language."""


_METAMODEL = metamodel_from_file(str(Path(__file__).with_name("candidate.tx")))


def build_candidate_profile(extracted: ExtractedData, normalized: NormalizedQualifications,
    classification: ClassificationResult,
    profile: Profile) -> CandidateProfile:
    """Join the results of the previous stages into one candidate profile."""
    return CandidateProfile(
        name=extracted.name,
        contact=extracted.contact,
        summary=extracted.summary,
        experience=extracted.experience,
        education=extracted.education,
        skills=list(dict.fromkeys(normalized.tokens)),  # recognized skills, no repeats
        evaluations=[
            Evaluation(
                profile_name=profile.name,
                accepted=classification.accepted,
                explanation=profile.get_explanation(classification.accepted),
            )
        ],
    )


def _text(value: str) -> str:
    """Write free text as a quoted STRING. Only double quotes need escaping."""
    return '"' + value.replace('"', '\\"') + '"'

def _personal_block(name: str) -> str:
    return f"candidate\n    name: {_text(name)}\nend"

def _contact_block(contact: ContactInfo) -> str:
    lines = []
    if contact.email:
        lines.append(f"    email: {contact.email}")  # lexical terminal, no quotes
    for field in ("phone", "location", "linkedin", "github"):
        value = getattr(contact, field)
        if value:
            lines.append(f"    {field}: {_text(value)}")
    return ("contact\n" + "\n".join(lines) + "\nend") if lines else ""

def _summary_block(summary: str) -> str:
    return f"summary: {_text(summary)}" if summary else ""

def _experience_block(entry: ExperienceEntry) -> str:
    lines = [f"    title: {_text(entry.title)}"]
    if entry.organization:
        lines.append(f"    organization: {_text(entry.organization)}")
    if entry.period:
        lines.append(f"    period: {_text(entry.period)}")
    lines += [f"    bullet: {_text(bullet)}" for bullet in entry.bullets]
    return "experience\n" + "\n".join(lines) + "\nend"

def _education_block(education: list[str]) -> str:
    return "\n".join(f"education: {_text(item)}" for item in education)

def _skills_block(skills: list[str]) -> str:
    return "skills: " + ", ".join(skills) if skills else ""

def _evaluation_block(evaluation: Evaluation) -> str:
    result = "ACCEPTED" if evaluation.accepted else "REJECTED"
    return (
        "evaluation\n"
        f"    profile: {_text(evaluation.profile_name)}\n"
        f"    result: {result}\n"
        f"    explanation: {_text(evaluation.explanation)}\n"
        "end"
    )


def to_dsl(candidate: CandidateProfile) -> str:
    """Write a candidate profile as text of the candidate language."""
    blocks = [
        _personal_block(candidate.name),
        _contact_block(candidate.contact),
        _summary_block(candidate.summary),
        *[_experience_block(entry) for entry in candidate.experience],
        _education_block(candidate.education),
        _skills_block(candidate.skills),
        *[_evaluation_block(evaluation) for evaluation in candidate.evaluations],
    ]
    return "\n\n".join(block for block in blocks if block) + "\n"

def parse_candidate(dsl_text: str):
    """Validate the text against the grammar and return the textX model."""
    try:
        return _METAMODEL.model_from_str(dsl_text)
    except TextXError as error:
        raise CandidateSyntaxError(str(error)) from error


def render_html(model) -> str:
    """Render a validated candidate model as a self-contained HTML page."""

    def esc(value) -> str:
        return html.escape(str(value), quote=True)

    def optional_contact(label: str, value: str | None) -> str:
        if not value:
            return ""
        return f"<p><strong>{esc(label)}:</strong> {esc(value)}</p>"

    contact = model.contact
    contact_html = ""

    if contact:
        contact_html = "".join([
            optional_contact("Email", contact.email),
            optional_contact("Phone", contact.phone),
            optional_contact("Location", contact.location),
            optional_contact("LinkedIn", contact.linkedin),
            optional_contact("GitHub", contact.github),
        ])

    summary_html = ""
    if model.summary:
        summary_html = f"""
        <div class="section">
            <h2>Profile Summary</h2>
            <p>{esc(model.summary)}</p>
        </div>
        """

    experience_html = ""
    if model.experiences:
        entries = []

        for experience in model.experiences:
            metadata = " · ".join(
                esc(value)
                for value in (experience.organization, experience.period)
                if value
            )

            metadata_html = (
                f'<p class="metadata">{metadata}</p>' if metadata else ""
            )

            bullets_html = "".join(
                f"<li>{esc(bullet)}</li>"
                for bullet in experience.bullets
            )

            entries.append(f"""
                <div class="experience-entry">
                    <h3>{esc(experience.title)}</h3>
                    {metadata_html}
                    {f"<ul>{bullets_html}</ul>" if bullets_html else ""}
                </div>
            """)

        experience_html = f"""
        <div class="section">
            <h2>Experience</h2>
            {"".join(entries)}
        </div>
        """

    education_html = ""
    if model.educations:
        education_items = "".join(
            f"<li>{esc(item.text)}</li>"
            for item in model.educations
        )
        education_html = f"""
        <div class="section">
            <h2>Education</h2>
            <ul>{education_items}</ul>
        </div>
        """

    skills_html = ""
    if model.skills:
        skill_items = "".join(
            f'<span class="skill">{esc(skill)}</span>'
            for skill in model.skills
        )
        skills_html = f"""
        <div class="section">
            <h2>Normalized Technical Skills</h2>
            <div class="skills">{skill_items}</div>
        </div>
        """

    evaluations_html = ""
    if model.evaluations:
        evaluation_items = []

        for evaluation in model.evaluations:
            accepted = evaluation.result == "ACCEPTED"
            status_class = "accepted" if accepted else "rejected"

            evaluation_items.append(f"""
                <div class="evaluation">
                    <p>
                        <strong>Profile evaluated:</strong>
                        {esc(evaluation.profile)}
                    </p>
                    <p>
                        <strong>Qualification pattern:</strong>
                        <span class="{status_class}">
                            {esc(evaluation.result)}
                        </span>
                    </p>
                    <p>{esc(evaluation.explanation)}</p>
                </div>
            """)

        evaluations_html = f"""
        <div class="section">
            <h2>Qualification Evaluation</h2>
            {"".join(evaluation_items)}
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ResumeLens - Candidate Profile</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            margin: 0;
            padding: 40px;
            color: #222;
        }}
        .candidate-card {{
            box-sizing: border-box;
            max-width: 850px;
            margin: auto;
            background-color: white;
            border: 1px solid #cccccc;
            border-radius: 10px;
            padding: 30px;
        }}
        .header {{
            border-bottom: 2px solid #333333;
            margin-bottom: 25px;
        }}
        .header h1 {{ margin-bottom: 5px; }}
        .header p {{ margin-top: 0; }}
        .section {{ margin-bottom: 25px; }}
        .section h2 {{
            border-bottom: 1px solid #dddddd;
            padding-bottom: 5px;
        }}
        .skills {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .skill {{
            background-color: #eeeeee;
            border-radius: 5px;
            padding: 8px 12px;
        }}
        .evaluation {{
            background-color: #eeeeee;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 12px;
        }}
        .accepted {{ font-weight: bold; color: #18733c; }}
        .rejected {{ font-weight: bold; color: #b42318; }}
        .metadata {{ font-size: 0.9em; color: #555; }}
        @media (max-width: 600px) {{
            body {{ padding: 12px; }}
            .candidate-card {{ padding: 18px; }}
        }}
    </style>
</head>
<body>
    <div class="candidate-card">
        <div class="header">
            <h1>{esc(model.personal.full_name)}</h1>
            <p>Candidate Profile generated by ResumeLens</p>
        </div>

        <div class="section">
            <h2>Personal Information</h2>
            {contact_html or "<p>No contact information available.</p>"}
        </div>

        {summary_html}
        {experience_html}
        {education_html}
        {skills_html}
        {evaluations_html}
    </div>
</body>
</html>
"""

