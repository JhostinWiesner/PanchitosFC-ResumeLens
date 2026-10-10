
import pytest

from core.catalog import Catalog
from core.ordering import OrderingError, order
from core.types import NormalizedQualifications


@pytest.fixture(scope="module")
def catalog() -> Catalog:
    return Catalog.from_json()


def make_normalized(tokens: list[str], unrecognized: list[str] | None = None):
    return NormalizedQualifications(
        tokens=tokens,
        unrecognized=unrecognized or [],
    )


# ---- entrada y salida básica --------------------------------------------

def test_order_empty_tokens_returns_empty_list(catalog):
    normalized = make_normalized([])

    assert order(normalized, "FULL_STACK", catalog) == []


def test_order_single_qualification(catalog):
    normalized = make_normalized(["PYTHON"])

    assert order(normalized, "DATA_ENGINEER", catalog) == ["PYTHON"]


# ---- filtrado por perfil -------------------------------------------------

def test_order_filters_qualifications_not_allowed_for_profile(catalog):
    normalized = make_normalized(
        ["REACT", "PYTHON", "DOCKER", "GIT"]
    )

    assert order(normalized, "DEVOPS", catalog) == [
        "PYTHON",
        "DOCKER",
        "GIT",
    ]


def test_shared_qualification_is_kept_for_allowed_profiles(catalog):
    normalized = make_normalized(["PYTHON"])

    for profile in ("FULL_STACK", "ML_ENGINEER", "DEVOPS", "DATA_ENGINEER"):
        assert order(normalized, profile, catalog) == ["PYTHON"]


def test_no_qualifications_match_profile(catalog):
    normalized = make_normalized(["REACT"])

    assert order(normalized, "ML_ENGINEER", catalog) == []


# ---- orden determinista --------------------------------------------------

def test_order_uses_fixed_category_order(catalog):
    normalized = make_normalized(
        ["POSTGRESQL", "REACT", "PYTHON", "JAVASCRIPT"]
    )

    assert order(normalized, "FULL_STACK", catalog) == [
        "JAVASCRIPT",
        "PYTHON",
        "REACT",
        "POSTGRESQL",
    ]


def test_order_within_category_uses_catalog_position(catalog):
    normalized = make_normalized(["KUBERNETES", "DOCKER"])

    assert order(normalized, "DEVOPS", catalog) == [
        "DOCKER",
        "KUBERNETES",
    ]


def test_order_is_independent_of_input_order(catalog):
    first = make_normalized(
        ["KUBERNETES", "PYTHON", "DOCKER", "GIT"]
    )
    second = make_normalized(
        ["GIT", "DOCKER", "KUBERNETES", "PYTHON"]
    )

    assert order(first, "DEVOPS", catalog) == order(
        second, "DEVOPS", catalog
    )


# ---- duplicados y términos desconocidos ---------------------------------

def test_order_removes_duplicate_canonical_qualifications(catalog):
    normalized = make_normalized(
        ["PYTHON", "KUBERNETES", "PYTHON", "DOCKER", "KUBERNETES"]
    )

    assert order(normalized, "DEVOPS", catalog) == [
        "PYTHON",
        "DOCKER",
        "KUBERNETES",
    ]


def test_unrecognized_terms_are_not_added_to_ordered_output(catalog):
    normalized = make_normalized(
        ["PYTHON"],
        unrecognized=["Rust", "tecnologia_inventada"],
    )

    assert order(normalized, "DEVOPS", catalog) == ["PYTHON"]
    assert normalized.unrecognized == ["Rust", "tecnologia_inventada"]


# ---- validación y manejo de errores -------------------------------------

def test_invalid_profile_raises_custom_error(catalog):
    normalized = make_normalized(["PYTHON"])

    with pytest.raises(
        OrderingError,
        match="Perfil no válido",
    ):
        order(normalized, "UNKNOWN_PROFILE", catalog)


def test_unknown_canonical_raises_custom_error(catalog):
    normalized = make_normalized(["PYTHON", "COBOL"])

    with pytest.raises(
        OrderingError,
        match="Calificación canónica no encontrada en el catálogo",
    ):
        order(normalized, "FULL_STACK", catalog)


# ---- no mutación de la entrada ------------------------------------------

def test_order_does_not_modify_normalized_input(catalog):
    normalized = make_normalized(
        ["KUBERNETES", "PYTHON", "DOCKER", "PYTHON"],
        unrecognized=["Rust"],
    )

    original_tokens = normalized.tokens.copy()
    original_unrecognized = normalized.unrecognized.copy()

    order(normalized, "DEVOPS", catalog)

    assert normalized.tokens == original_tokens
    assert normalized.unrecognized == original_unrecognized
