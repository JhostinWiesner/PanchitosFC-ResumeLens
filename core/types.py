from dataclasses import dataclass, field
from typing import Optional

@dataclass(frozen=True)
class ContactInfo:
    """Extracted contact information."""
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None


@dataclass(frozen=True)
class ExperienceEntry:
    """Structured representation of a single experience entry."""
    title: str
    organization: str
    period: str
    bullets: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Contracts for the data structures used in the pipeline.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ExtractedData:
    name: str
    contact: ContactInfo
    summary: str
    skills_raw: list[str]
    education: list[str]
    experience: list[ExperienceEntry]

@dataclass(frozen=True)
class NormalizedQualifications:
    tokens: list[str]      # canonical, unordered
    unrecognized: list[str]  # what FST could not recognize

@dataclass(frozen=True)
class OrderedQualifications:
    profile_name: str
    sequence: list[str]

@dataclass(frozen=True)
class ClassificationResult:
    profile_name: str
    accepted: bool