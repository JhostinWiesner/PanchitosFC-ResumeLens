
import pytest

from core.catalog import Catalog
from core.ordering import order
from core.types import NormalizedQualifications
from profiles.dev_ops import DEVOPS


@pytest.fixture(scope="module")
def catalog() -> Catalog:
    return Catalog.from_json()


def make_normalized(tokens: list[str], unrecognized=None):
    return NormalizedQualifications(
        tokens=tokens,
        unrecognized=unrecognized or [],
    )


def test_order_returns_ordered_qualifications(catalog):
    normalized = make_normalized(
        ["GIT", "AWS", "DOCKER", "PYTHON"]
    )

    result = order(normalized, DEVOPS, catalog)

    assert result.profile_name == "DevOps Engineer"
    assert result.sequence == ["PYTHON", "DOCKER", "AWS", "GIT"]


def test_order_filters_qualifications_outside_profile(catalog):
    normalized = make_normalized(
        ["REACT", "PYTHON", "DOCKER", "GIT"]
    )

    result = order(normalized, DEVOPS, catalog)

    assert result.sequence == ["PYTHON", "DOCKER", "GIT"]


def test_order_removes_duplicates(catalog):
    normalized = make_normalized(
        ["PYTHON", "DOCKER", "PYTHON", "GIT", "DOCKER"]
    )

    result = order(normalized, DEVOPS, catalog)

    assert result.sequence == ["PYTHON", "DOCKER", "GIT"]


def test_order_uses_profile_category_order(catalog):
    normalized = make_normalized(
        ["GIT", "AWS", "TERRAFORM", "JENKINS", "KUBERNETES", "BASH"]
    )

    result = order(normalized, DEVOPS, catalog)

    assert result.sequence == [
        "BASH",
        "KUBERNETES",
        "JENKINS",
        "TERRAFORM",
        "AWS",
        "GIT",
    ]


def test_order_empty_tokens(catalog):
    normalized = make_normalized([])

    result = order(normalized, DEVOPS, catalog)

    assert result.profile_name == "DevOps Engineer"
    assert result.sequence == []


def test_order_preserves_input(catalog):
    normalized = make_normalized(
        ["GIT", "PYTHON", "DOCKER"],
        unrecognized=["UnknownTool"],
    )

    original_tokens = normalized.tokens.copy()
    original_unrecognized = normalized.unrecognized.copy()

    order(normalized, DEVOPS, catalog)

    assert normalized.tokens == original_tokens
    assert normalized.unrecognized == original_unrecognized


def test_order_preserves_unrecognized_terms(catalog):
    normalized = make_normalized(
        ["PYTHON", "DOCKER"],
        unrecognized=["UnknownTool"],
    )

    result = order(normalized, DEVOPS, catalog)

    assert result.sequence == ["PYTHON", "DOCKER"]
    assert normalized.unrecognized == ["UnknownTool"]


def test_order_rejects_unknown_canonical_qualification(catalog):
    normalized = make_normalized(["NOT_A_REAL_QUALIFICATION"])

    with pytest.raises(KeyError):
        order(normalized, DEVOPS, catalog)