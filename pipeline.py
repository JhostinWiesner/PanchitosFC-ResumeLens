from core.catalog import Catalog
from core.extraction import extract
from core.grammar.grammar import build_candidate_profile, parse_candidate, to_dsl
from core.normalization import normalize
from core.ordering import order
from core.recognition import recognize
from core.types import PipelineResult
from profiles.base import Profile


def run(resume_text: str, profile: Profile, catalog: Catalog) -> PipelineResult:
    """Execute the full pipeline for a résumé text and a profile."""

    # Stage 1: extraction (global regex)
    extracted = extract(resume_text)

    # Stage 2: normalization (global FST) and ordering (by the profile's category order)
    normalized = normalize(extracted, catalog)
    ordered = order(normalized, profile, catalog)

    # Stage 3: recognition (DFA of the profile)
    classification = recognize(ordered, profile, catalog)

    # Stage 4: candidate profile language
    candidate = build_candidate_profile(extracted, normalized, classification, profile)
    dsl_text = to_dsl(candidate)
    parse_candidate(dsl_text)  # raises CandidateSyntaxError if the text breaks the grammar

    return PipelineResult(extracted, normalized, ordered, classification, candidate, dsl_text)