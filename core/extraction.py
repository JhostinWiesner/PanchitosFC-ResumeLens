"""Stage 1: permissive résumé extraction using Python's :mod:`re` module.

This module captures candidate information as written. It does not canonicalize
qualifications or decide whether a candidate matches a professional profile.
"""
from __future__ import annotations

import re

from core.types import ContactInfo, ExperienceEntry, ExtractedData


# Keep headings anchored to a complete line so a heading mentioned in prose does
# not accidentally split a section. Horizontal whitespace is intentional here:
# using ``\s`` could consume newlines in multiline mode.
SECTION_PATTERNS: dict[str, str] = {
    "skills": r"(?:technical\s+skills|skills|technologies|tech\s+stack)",
    "experience": r"(?:professional\s+experience|work\s+experience|experience|employment)",
    "education": r"(?:academic\s+background|academic\s+qualifications|education)",
}
ANY_SECTION_HEADER = re.compile(
    r"(?im)^[ \t]*(?:" + "|".join(SECTION_PATTERNS.values()) + r")[ \t]*:?[ \t]*$"
)
SECTION_HEADER_PATTERNS = {
    key: re.compile(r"(?i)^(?:" + value + r")$")
    for key, value in SECTION_PATTERNS.items()
}

EMAIL = re.compile(r"[A-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Z0-9](?:[A-Z0-9-]*[A-Z0-9])?(?:\.[A-Z0-9](?:[A-Z0-9-]*[A-Z0-9])?)+", re.IGNORECASE)
PHONE = re.compile(
    r"(?<!\w)(?:\+?\d{1,3}[ .()-]?)?(?:\(?\d{2,4}\)?[ .-]?)\d{3,4}[ .-]?\d{3,4}(?!\w)"
)
LINKEDIN = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+", re.IGNORECASE)
GITHUB = re.compile(r"(?:https?://)?(?:www\.)?github\.com/[\w-]+", re.IGNORECASE)
LOCATION_LABELED = re.compile(
    r"(?im)^[ \t]*(?:location|based[ \t]+in|address)[ \t]*:[ \t]*(.+?)[ \t]*$"
)
# Unlabeled locations are only searched in the contact/header area, never inside
# skills, education, or experience sections. This avoids treating "Python, Java"
# as a city/country pair.
LOCATION_INLINE = re.compile(
    r"^[ \t]*([A-ZÀ-ÖØ-Þ][A-Za-zÀ-ÖØ-öø-ÿ.'’ -]*?)\s*,\s*"
    r"([A-ZÀ-ÖØ-Þ][A-Za-zÀ-ÖØ-öø-ÿ.'’ -]*?)[ \t]*$"
)

NAME = re.compile(
    r"^[A-ZÀ-ÖØ-Þ][A-Za-zÀ-ÖØ-öø-ÿ'’.-]*"
    r"(?:[ \t]+[A-ZÀ-ÖØ-Þ][A-Za-zÀ-ÖØ-öø-ÿ'’.-]*){1,3}$"
)
SKILL_DELIMITER = re.compile(r"[,;\n]+")
BULLET_LINE = re.compile(r"^[ \t]*[•●▪*\-][ \t]+(.+?)[ \t]*$")
PERIOD = re.compile(
    r"(?i)(?<!\d)(?:19|20)\d{2}[ \t]*(?:[-–—]|\bto\b)[ \t]*"
    r"(?:(?:19|20)\d{2}|present\b|current\b)(?!\w)"
)
ORG_PERIOD_LINE = re.compile(
    r"^[ \t]*(?P<organization>[^|·]+?)[ \t]*[|·][ \t]*(?P<period>.+?)[ \t]*$"
)

# Do not strip internal punctuation: React.js, Node.js, scikit-learn and .NET
# must remain valid raw candidates. Only boundary punctuation is removed.
_EDGE_PUNCTUATION = " \t\r\n,;:!?()[]{}\"“”‘’"
_URL_TRAILING_PUNCTUATION = ".,;:!?)]}\"”’"


def _clean_edge_punctuation(value: str) -> str:
    """Trim whitespace and surrounding punctuation, preserving internal text."""
    return value.strip().strip(_EDGE_PUNCTUATION).strip()


def _section_spans(text: str) -> dict[str, str]:
    """Return the first content block for each recognized section heading."""
    matches = list(ANY_SECTION_HEADER.finditer(text))
    sections: dict[str, str] = {}

    for index, match in enumerate(matches):
        heading = match.group(0).strip().rstrip(":").strip()
        key = next(
            (
                name
                for name, pattern in SECTION_HEADER_PATTERNS.items()
                if pattern.fullmatch(heading)
            ),
            None,
        )
        if key is None:
            continue

        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        # Do not silently merge repeated headings into one section.
        sections.setdefault(key, text[start:end].strip())

    return sections


def _first_section_start(text: str) -> int:
    """Return the start of the first recognized section, or the text length."""
    match = ANY_SECTION_HEADER.search(text)
    return match.start() if match else len(text)


def _extract_name(text: str) -> str:
    """Find a plausible 2–4-word name near the beginning of the résumé."""
    header = text[:_first_section_start(text)]
    for line in header.splitlines()[:5]:
        candidate = line.strip()
        if not candidate:
            continue
        if EMAIL.search(candidate) or PHONE.search(candidate):
            continue
        if LINKEDIN.search(candidate) or GITHUB.search(candidate):
            continue
        match = NAME.fullmatch(candidate)
        if match:
            return _clean_edge_punctuation(match.group(0))
    return ""


def _find_phone(text: str) -> str | None:
    """Find a phone-like value while rejecting obvious year ranges."""
    for match in PHONE.finditer(text):
        candidate = _clean_edge_punctuation(match.group(0))
        digits = re.sub(r"\D", "", candidate)
        # Dates such as 2021-2023 are not contact phone numbers.
        if PERIOD.fullmatch(candidate):
            continue
        if 7 <= len(digits) <= 15:
            return candidate
    return None


def _extract_contact(text: str) -> ContactInfo:
    """Extract contact values from the whole résumé without reading skills as location."""
    email_match = EMAIL.search(text)
    phone = _find_phone(text)
    linkedin_match = LINKEDIN.search(text)
    github_match = GITHUB.search(text)

    labeled_location = LOCATION_LABELED.search(text)
    location: str | None = None
    if labeled_location:
        location = _clean_edge_punctuation(labeled_location.group(1)) or None
    else:
        # An unlabeled city/country pair is only plausible in the header/contact
        # area. Do not scan the skills or education blocks for comma-separated text.
        header = text[:_first_section_start(text)]
        for line in header.splitlines():
            candidate = line.strip()
            match = LOCATION_INLINE.fullmatch(candidate)
            if match:
                location = _clean_edge_punctuation(candidate) or None
                break

    return ContactInfo(
        email=_clean_edge_punctuation(email_match.group(0)) if email_match else None,
        phone=phone,
        location=location,
        linkedin=(linkedin_match.group(0).rstrip(_URL_TRAILING_PUNCTUATION) if linkedin_match else None),
        github=(github_match.group(0).rstrip(_URL_TRAILING_PUNCTUATION) if github_match else None),
    )


def _is_contact_line(line: str) -> bool:
    """Return whether a header line consists of recognizable contact data."""
    return bool(
        EMAIL.search(line)
        or _find_phone(line)
        or LINKEDIN.search(line)
        or GITHUB.search(line)
        or LOCATION_LABELED.match(line)
        or LOCATION_INLINE.fullmatch(line.strip())
    )


def _extract_summary(text: str, name: str) -> str:
    """Capture free text before the first section, excluding name/contact lines."""
    header = text[:_first_section_start(text)]
    kept: list[str] = []

    for line in header.splitlines():
        candidate = line.strip()
        if not candidate or (name and candidate == name):
            if not candidate and kept and kept[-1] != "":
                kept.append("")
            continue
        if _is_contact_line(candidate):
            continue
        kept.append(candidate)

    return "\n".join(kept).strip()


def _extract_skills(section: str | None) -> list[str]:
    """Split the isolated skills section into raw, non-empty candidates."""
    if not section:
        return []
    result: list[str] = []
    for token in SKILL_DELIMITER.split(section):
        cleaned = _clean_edge_punctuation(token).rstrip(".").strip()
        if cleaned:
            result.append(cleaned)
    return result


def _extract_education(section: str | None) -> list[str]:
    """Keep each non-empty education line as a raw entry."""
    if not section:
        return []
    entries: list[str] = []
    for line in section.splitlines():
        cleaned = re.sub(r"^[ \t]*[•●▪*\-][ \t]*", "", line).strip()
        cleaned = _clean_edge_punctuation(cleaned)
        if cleaned:
            entries.append(cleaned)
    return entries


def _experience_entry_from_anchor(lines: list[str], anchor_index: int, next_anchor: int) -> ExperienceEntry | None:
    """Build an experience entry from a line containing its date range."""
    date_line = lines[anchor_index]
    period_match = PERIOD.search(date_line)
    if not period_match:
        return None

    title_index = anchor_index - 1
    organization = ""
    org_period_match = ORG_PERIOD_LINE.fullmatch(date_line)

    if org_period_match:
        # Common format: title on one line, then "Organization | period".
        organization = _clean_edge_punctuation(org_period_match.group("organization"))
    elif date_line.strip() == period_match.group(0).strip() and anchor_index >= 2:
        # Also support the three-line format: title, organization, period.
        title_index = anchor_index - 2
        organization = _clean_edge_punctuation(lines[anchor_index - 1])
    else:
        before_period = date_line[:period_match.start()]
        after_period = date_line[period_match.end():]
        organization = _clean_edge_punctuation(before_period.strip(" |·—–-"))
        if not organization and after_period.strip():
            organization = _clean_edge_punctuation(after_period.strip(" |·—–-"))

    if title_index < 0:
        return None
    title = _clean_edge_punctuation(lines[title_index])
    if not title or BULLET_LINE.match(lines[title_index]):
        return None

    period = _clean_edge_punctuation(period_match.group(0))
    bullets: list[str] = []
    for line in lines[anchor_index + 1:next_anchor]:
        bullet_match = BULLET_LINE.fullmatch(line)
        if bullet_match:
            bullet = _clean_edge_punctuation(bullet_match.group(1))
            if bullet:
                bullets.append(bullet)

    return ExperienceEntry(title=title, organization=organization, period=period, bullets=bullets)


def _extract_experience(section: str | None) -> list[ExperienceEntry]:
    """Extract experience entries, using date ranges as anchors when available."""
    if not section:
        return []

    # Normalize line endings and remove blank lines without changing line order.
    lines = [line.strip() for line in section.replace("\r\n", "\n").replace("\r", "\n").splitlines() if line.strip()]
    if not lines:
        return []

    anchors = [
        index for index, line in enumerate(lines)
        if not BULLET_LINE.fullmatch(line) and PERIOD.search(line)
    ]
    if anchors:
        entries: list[ExperienceEntry] = []
        for position, anchor_index in enumerate(anchors):
            next_anchor = anchors[position + 1] if position + 1 < len(anchors) else len(lines)
            entry = _experience_entry_from_anchor(lines, anchor_index, next_anchor)
            if entry is not None:
                entries.append(entry)
        if entries:
            return entries

    # Fallback for résumé fragments that omit dates: preserve a minimally useful
    # title/block rather than inventing organization or period values.
    entries = []
    blocks = [block for block in re.split(r"\n[ \t]*\n", section.strip()) if block.strip()]
    for block in blocks:
        block_lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not block_lines:
            continue
        title = _clean_edge_punctuation(block_lines[0])
        organization = ""
        period = ""
        bullets: list[str] = []
        for line in block_lines[1:]:
            bullet_match = BULLET_LINE.fullmatch(line)
            if bullet_match:
                bullet = _clean_edge_punctuation(bullet_match.group(1))
                if bullet:
                    bullets.append(bullet)
                continue
            org_period_match = ORG_PERIOD_LINE.fullmatch(line)
            if org_period_match:
                organization = _clean_edge_punctuation(org_period_match.group("organization"))
                date_match = PERIOD.search(org_period_match.group("period"))
                period = _clean_edge_punctuation(date_match.group(0)) if date_match else _clean_edge_punctuation(org_period_match.group("period"))
            elif PERIOD.search(line):
                date_match = PERIOD.search(line)
                period = _clean_edge_punctuation(date_match.group(0)) if date_match else ""
                organization = _clean_edge_punctuation(PERIOD.sub("", line).strip(" |·—–-"))
        if title:
            entries.append(ExperienceEntry(title=title, organization=organization, period=period, bullets=bullets))
    return entries


def extract(resume_text: str) -> ExtractedData:
    """Extract raw résumé fields using regex; do not normalize or classify."""
    if not isinstance(resume_text, str):
        raise TypeError("resume_text must be a string")

    # Normalize line endings so anchored, multiline expressions behave uniformly.
    text = resume_text.replace("\r\n", "\n").replace("\r", "\n")
    sections = _section_spans(text)
    name = _extract_name(text)

    return ExtractedData(
        name=name,
        contact=_extract_contact(text),
        summary=_extract_summary(text, name),
        skills_raw=_extract_skills(sections.get("skills")),
        education=_extract_education(sections.get("education")),
        experience=_extract_experience(sections.get("experience")),
    )
