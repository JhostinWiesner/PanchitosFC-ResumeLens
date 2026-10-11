from __future__ import annotations

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
