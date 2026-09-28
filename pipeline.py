from core.types import (
    ExtractedData,
    NormalizedQualifications,
    OrderedQualifications,
    ClassificationResult,
)
from profiles.base import Profile
from core.extraction import extract
from core.normalization import normalize, order
from core.recognition import recognize


def run(
    resume_text: str,
    profile: Profile
) -> tuple[ExtractedData, NormalizedQualifications, OrderedQualifications, ClassificationResult]:
    """Execute the full pipeline for a given resume text and profile."""
    
    # Stage 1: Extraction (Global Regex)
    extracted: ExtractedData = extract(resume_text)
    
    # Stage 2: Normalization (Global FST)
    normalized: NormalizedQualifications = normalize(extracted)
    
    # Stage 3: Ordering (By canonical order of the profile)
    ordered: OrderedQualifications = order(normalized, profile)
    
    # Stage 4: Recognition (Automaton of the profile)
    classification: ClassificationResult = recognize(ordered, profile)
    
    return extracted, normalized, ordered, classification