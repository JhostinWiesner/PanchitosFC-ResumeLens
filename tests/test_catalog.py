import json

import pytest

from core.catalog import Catalog, CatalogError, name_variants, normalize_text


@pytest.fixture(scope="module")
def catalog() -> Catalog:
    return Catalog.from_json()


VALID_PROFILES = ["FULL_STACK", "ML_ENGINEER", "DEVOPS", "DATA_ENGINEER"]


def entry(canonical="PYTHON", category="LANGUAGE", aliases=("py",), profiles=("ML_ENGINEER",)):
    return {
        "canonical": canonical,
        "category": category,
        "aliases": list(aliases),
        "profiles": list(profiles),
    }


def write(tmp_path, qualifications):
    path = tmp_path / "catalog.json"
    path.write_text(
        json.dumps({"profiles": VALID_PROFILES, "qualifications": qualifications}),
        encoding="utf-8",
    )
    return path


# ---- carga del catálogo real -------------------------------------------
def test_loads_real_catalog(catalog):
    assert len(catalog) == 39
    assert "KUBERNETES" in catalog


def test_every_canonical_resolves_to_itself(catalog):
    for q in catalog:
        assert catalog.normalize(q.canonical) == q.canonical


# ---- aliases y variantes (opción A) ------------------------------------
@pytest.mark.parametrize(
    "raw, expected",
    [
        ("JS", "JAVASCRIPT"),
        ("Javascript", "JAVASCRIPT"),
        ("React.js", "REACT"),
        ("  react.JS ", "REACT"),
        ("Postgres", "POSTGRESQL"),
        ("PostgreSQL", "POSTGRESQL"),
        ("Python", "PYTHON"),  # variante del canónico, no está en aliases
        ("Docker", "DOCKER"),
        ("node js", "NODE_JS"),
        ("Scikit-Learn", "SCIKIT_LEARN"),
        ("scikit learn", "SCIKIT_LEARN"),
        ("Google   Cloud  Platform", "GCP"),
        ("K8s", "KUBERNETES"),
        ("GitHub Actions", "GITHUB_ACTIONS"),
        ("gIt", "GIT"),
    ],
)
def test_normalize_known_texts(catalog, raw, expected):
    assert catalog.normalize(raw) == expected


@pytest.mark.parametrize("raw", ["Fortran", "", "   ", "react native"])
def test_normalize_unknown_returns_none(catalog, raw):
    assert catalog.normalize(raw) is None


def test_name_variants():
    assert name_variants("PYTHON") == ("python",)
    assert set(name_variants("NODE_JS")) == {"node js", "node-js", "node.js", "nodejs", "node_js"}


def test_normalize_text():
    assert normalize_text("  Node\u00a0 JS ") == "node js"


# ---- consulta ----------------------------------------------------------
def test_category_and_position(catalog):
    assert catalog.category_of("GIT") == "VCS"
    assert catalog.position("DOCKER") < catalog.position("KUBERNETES")
    assert catalog.position("JAVASCRIPT") < catalog.position("TYPESCRIPT")
    assert catalog.get("JAVA").profiles == ("FULL_STACK",)


def test_qualifications_for_returns_file_order(catalog):
    assert catalog.qualifications_for("FULL_STACK", "LANGUAGE") == (
        "JAVASCRIPT",
        "TYPESCRIPT",
        "JAVA",
        "PYTHON",
    )
    assert catalog.qualifications_for("DATA_ENGINEER", "LANGUAGE") == ("PYTHON",)


def test_categories_in_first_appearance_order(catalog):
    assert catalog.categories[0] == "LANGUAGE"
    assert catalog.categories[-1] == "VCS"


def test_unknown_canonical_raises(catalog):
    with pytest.raises(KeyError):
        catalog.category_of("COBOL")


def test_terms_longest_first(catalog):
    terms = catalog.terms_longest_first()
    assert terms == sorted(terms, key=lambda t: (-len(t), t))
    assert terms.index("google cloud platform") < terms.index("google cloud")


def test_surface_forms_cover_aliases(catalog):
    forms = catalog.surface_forms()
    assert forms["js"] == "JAVASCRIPT"
    assert forms["amazon web services"] == "AWS"


# ---- validación (casos de rechazo) --------------------------------------
def test_rejects_duplicate_canonical(tmp_path):
    path = write(tmp_path, [entry(), entry(aliases=("py3",))])
    with pytest.raises(CatalogError, match="repetido"):
        Catalog.from_json(path)


def test_rejects_alias_shared_by_two_entries(tmp_path):
    path = write(tmp_path, [entry(aliases=("sh",)), entry("BASH", aliases=("SH",))])
    with pytest.raises(CatalogError, match="dos calificaciones"):
        Catalog.from_json(path)


def test_rejects_bad_canonical_format(tmp_path):
    path = write(tmp_path, [entry("Node.js")])
    with pytest.raises(CatalogError, match="MAYUSCULAS"):
        Catalog.from_json(path)


def test_rejects_missing_field(tmp_path):
    path = write(tmp_path, [{"canonical": "GIT", "category": "VCS"}])
    with pytest.raises(CatalogError, match="faltan campos"):
        Catalog.from_json(path)


def test_rejects_missing_profiles_field(tmp_path):
    qualification = entry()
    del qualification["profiles"]
    path = write(tmp_path, [qualification])
    with pytest.raises(CatalogError, match="faltan campos"):
        Catalog.from_json(path)


def test_rejects_duplicate_profiles(tmp_path):
    path = write(tmp_path, [entry(profiles=("ML_ENGINEER", "ML_ENGINEER"))])
    with pytest.raises(CatalogError, match="repetidos"):
        Catalog.from_json(path)


def test_rejects_unknown_profile(tmp_path):
    path = write(tmp_path, [entry(profiles=("UNKNOWN",))])
    with pytest.raises(CatalogError, match="no definidos"):
        Catalog.from_json(path)


def test_rejects_invalid_aliases(tmp_path):
    path = write(tmp_path, [entry(aliases=("ok", "  "))])
    with pytest.raises(CatalogError, match="aliases"):
        Catalog.from_json(path)


def test_rejects_missing_file_and_bad_json(tmp_path):
    with pytest.raises(CatalogError, match="No existe"):
        Catalog.from_json(tmp_path / "nope.json")
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(CatalogError, match="JSON inválido"):
        Catalog.from_json(bad)