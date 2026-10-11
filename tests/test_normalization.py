from core.catalog import Catalog
from core.normalization import normalize
from core.types import (
    ContactInfo,
    ExperienceEntry,
    ExtractedData,
    NormalizedQualifications,
)

import pytest


@pytest.fixture
def catalog() -> Catalog:
    return Catalog.from_json()


def make_extracted(skills: list[str]) -> ExtractedData:
    return ExtractedData(
        name="Test User",
        contact=ContactInfo(),
        summary="",
        skills_raw=skills,
        education=[],
        experience=[],
    )


def test_normalize_all_catalog_spellings(catalog):
    spellings = catalog.spellings()

    result = normalize(make_extracted(list(spellings)), catalog)

    assert isinstance(result, NormalizedQualifications)
    assert result.tokens == list(spellings.values())
    assert result.unrecognized == []


def test_normalize_aliases_and_variants(catalog):
    extracted = make_extracted([
        "JS",
        "  React.JS ",
        "Scikit-Learn",
        "Google   Cloud  Platform",
        "K8s",
    ])

    result = normalize(extracted, catalog)

    assert result.tokens == [
        "JAVASCRIPT",
        "REACT",
        "SCIKIT_LEARN",
        "GCP",
        "KUBERNETES",
    ]
    assert result.unrecognized == []


def test_unknown_candidates_are_preserved(catalog):
    extracted = make_extracted([
        "Rust",
        "tecnologia_inventada",
        "pythonx",
    ])

    result = normalize(extracted, catalog)

    assert result.tokens == []
    assert result.unrecognized == [
        "Rust",
        "tecnologia_inventada",
        "pythonx",
    ]


def test_mixed_known_and_unknown_candidates(catalog):
    extracted = make_extracted([
        "Python",
        "Rust",
        "PyTorch",
        "UnknownTech",
    ])

    result = normalize(extracted, catalog)

    assert result.tokens == ["PYTHON", "PYTORCH"]
    assert result.unrecognized == ["Rust", "UnknownTech"]


def test_duplicate_candidates_are_preserved(catalog):
    extracted = make_extracted([
        "Python",
        "PYTHON",
        "py",
    ])

    result = normalize(extracted, catalog)

    assert result.tokens == ["PYTHON", "PYTHON", "PYTHON"]
    assert result.unrecognized == []


def test_blank_candidates_are_ignored(catalog):
    extracted = make_extracted([
        "",
        "   ",
        "\t",
        "Python",
    ])

    result = normalize(extracted, catalog)

    assert result.tokens == ["PYTHON"]
    assert result.unrecognized == []


def test_empty_skills_list(catalog):
    result = normalize(make_extracted([]), catalog)

    assert result.tokens == []
    assert result.unrecognized == []
