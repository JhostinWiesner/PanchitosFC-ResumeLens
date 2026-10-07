import re

from core.types import ContactInfo, ExperienceEntry, ExtractedData


# Regular expressions defined for Stage 1.
# The specific patterns will be added once they are defined.
REGEX_PATTERNS: dict[str, str] = {}


def _find_all(pattern: str, text: str) -> list[str]:
    """Return all matches of a regular expression in the given text."""
    return re.findall(pattern, text, re.IGNORECASE)


def _find_first(pattern: str, text: str) -> str:
    """Return the first match of a regular expression, or an empty string."""
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(0) if match else ""


def extract(resume_text: str) -> ExtractedData:
    """
    Extract raw information from a résumé using regular expressions.

    The regular expressions used by this function will be defined
    according to the categories established for Stage 1.
    """

    extracted_data = {
        "name": "",
        "contact": ContactInfo(),
        "summary": "",
        "skills_raw": [],
        "education": [],
        "experience": [],
    }

    # The specific extraction rules will be connected here
    # once the regular expressions are defined.

    return ExtractedData(**extracted_data)