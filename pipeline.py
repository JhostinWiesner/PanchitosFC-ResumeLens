from core.types import (
    ExtractedData,
    NormalizedQualifications,
    OrderedQualifications,
    ClassificationResult,
)
from profiles.base import Profile
from core.extraction import extract
from core.normalization import normalize
from core.ordering import order
from core.recognition import recognize
from core.catalog import Catalog


def run(
    resume_text: str,
    profile: Profile,
    catalog: Catalog
) -> tuple[ExtractedData, NormalizedQualifications, OrderedQualifications, ClassificationResult]:
    """Execute the full pipeline for a given resume text and profile."""
    
    # Stage 1: extraction (global regex)
    extracted = extract(resume_text)

    # Stage 2: normalization (global FST) and ordering (by the profile's category order)
    normalized = normalize(extracted, catalog)
    ordered = order(normalized, profile, catalog)

    # Stage 3: recognition (DFA of the profile)
    classification = recognize(ordered, profile, catalog)

    return extracted, normalized, ordered, classification