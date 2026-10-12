import pytest

from core.catalog import Catalog
from core.recognition import build_automaton, recognize
from core.types import OrderedQualifications
from profiles.base import Profile
from profiles.data_engineer import DATA_ENGINEER
from profiles.full_stack import FULL_STACK


PROFILES = {
    "FULL_STACK": FULL_STACK,
    "ML_ENGINEER": Profile(
        "ML_ENGINEER",
        "Machine Learning Engineer",
        ("LANGUAGE", "ML_LIBRARY", "DATABASE", "VCS"),
    ),
    "DEVOPS": Profile(
        "DEVOPS",
        "DevOps Engineer",
        ("LANGUAGE", "CONTAINER", "CI_CD", "IAC", "CLOUD", "VCS"),
    ),
    "DATA_ENGINEER": DATA_ENGINEER,
}

MISSING_CASES = [
    (profile_id, index)
    for profile_id, profile in PROFILES.items()
    for index in range(len(profile.canonical_order))
]


@pytest.fixture(scope="session")
def catalog() -> Catalog:
    return Catalog.from_json()


@pytest.fixture(scope="session")
def profiles() -> dict[str, Profile]:
    return PROFILES


def accepted(
    profile: Profile, symbols: list[str], catalog: Catalog
) -> bool:
    ordered = OrderedQualifications(profile.name, symbols)
    return recognize(ordered, profile, catalog).accepted


def test_data_engineer_profile_configuration():
    assert DATA_ENGINEER.identifier == "DATA_ENGINEER"
    assert DATA_ENGINEER.name == "Data Engineer"
    assert DATA_ENGINEER.canonical_order == (
        "LANGUAGE",
        "DATABASE",
        "DATA_PROCESSING",
        "WORKFLOW",
        "CLOUD",
        "VCS",
    )


def test_dfa_structure(catalog, profiles):
    """TC-01: the Full Stack DFA has the documented structure."""
    automaton = build_automaton(catalog, profiles["FULL_STACK"])

    assert len(automaton.states) == 6, "Full Stack DFA should contain q0 through q5"
    assert {state.value for state in automaton.start_states} == {"q0"}, (
        "The DFA start state should be q0"
    )
    assert {state.value for state in automaton.final_states} == {"q5"}, (
        "Only q5 should be a final state"
    )
    assert automaton.is_deterministic(), "The recognition automaton must be deterministic"


def test_full_stack_groups_match_documentation(catalog):
    """TC-02: catalog groups match the Stage 3 documentation."""
    expected_groups = {
        "LANGUAGE": ("JAVASCRIPT", "TYPESCRIPT", "JAVA", "PYTHON"),
        "FRONTEND": ("REACT", "ANGULAR", "VUE"),
        "BACKEND": ("NODE_JS", "DJANGO", "SPRING_BOOT", "REST_API"),
        "DATABASE": ("SQL", "POSTGRESQL", "MONGODB"),
        "VCS": ("GIT",),
    }

    for category, expected in expected_groups.items():
        assert set(catalog.qualifications_for("FULL_STACK", category)) == set(expected), (
            f"FULL_STACK {category} group differs from the Stage 3 documentation"
        )


@pytest.mark.parametrize(
    ("profile_id", "symbols"),
    [
        ("FULL_STACK", ["JAVASCRIPT", "REACT", "NODE_JS", "POSTGRESQL", "GIT"]),
        ("ML_ENGINEER", ["PYTHON", "PANDAS", "TENSORFLOW", "POSTGRESQL", "GIT"]),
        ("FULL_STACK", ["TYPESCRIPT", "ANGULAR", "DJANGO", "MONGODB", "GIT"]),
        (
            "FULL_STACK",
            [
                "JAVASCRIPT",
                "TYPESCRIPT",
                "REACT",
                "NODE_JS",
                "SQL",
                "POSTGRESQL",
                "GIT",
            ],
        ),
        ("DEVOPS", ["PYTHON", "DOCKER", "GITHUB_ACTIONS", "TERRAFORM", "AWS", "GIT"]),
        ("DATA_ENGINEER", ["PYTHON", "POSTGRESQL", "SPARK", "AIRFLOW", "AWS", "GIT"]),
    ],
    ids=["TC-03", "TC-04", "TC-05", "TC-06", "TC-07", "TC-08"],
)
def test_accepted_documented_sequences(catalog, profiles, profile_id, symbols):
    """TC-03 to TC-08: documented valid sequences are accepted."""
    profile = profiles[profile_id]
    assert accepted(profile, symbols, catalog), (
        f"{profile_id} should accept the documented sequence {symbols}"
    )


@pytest.mark.parametrize(
    "profile_id",
    list(PROFILES),
    ids=[f"TC-09-{profile_id}" for profile_id in PROFILES],
)
def test_one_symbol_per_category_for_each_profile(catalog, profiles, profile_id):
    """TC-09: one catalog symbol per category is accepted for every profile."""
    profile = profiles[profile_id]
    symbols = [
        catalog.qualifications_for(profile.identifier, category)[0]
        for category in profile.canonical_order
    ]

    assert accepted(profile, symbols, catalog), (
        f"{profile_id} should accept one qualification from every category"
    )


@pytest.mark.parametrize(
    ("profile_id", "missing_index"),
    MISSING_CASES,
    ids=[f"TC-10-{profile_id}-{index}" for profile_id, index in MISSING_CASES],
)
def test_missing_one_category_is_rejected(catalog, profiles, profile_id, missing_index):
    """TC-10: removing any category rejects every profile sequence."""
    profile = profiles[profile_id]
    symbols = [
        catalog.qualifications_for(profile.identifier, category)[0]
        for category in profile.canonical_order
    ]
    missing = symbols.pop(missing_index)

    assert not accepted(profile, symbols, catalog), (
        f"{profile_id} should reject the sequence missing {missing}"
    )


@pytest.mark.parametrize(
    ("symbols", "description"),
    [
        (["JAVASCRIPT", "REACT", "NODE_JS", "POSTGRESQL"], "missing version control"),
        (["REACT", "NODE_JS", "SQL", "GIT"], "missing language"),
        (["JAVASCRIPT"], "only the first group"),
        (["GIT"], "only the last group"),
        ([], "empty sequence"),
    ],
    ids=["TC-11", "TC-12", "TC-13", "TC-14", "TC-15"],
)
def test_incomplete_full_stack_sequences_are_rejected(catalog, profiles, symbols, description):
    """TC-11 to TC-15: incomplete Full Stack sequences are rejected."""
    assert not accepted(profiles["FULL_STACK"], symbols, catalog), (
        f"Full Stack should reject the {description} sequence"
    )


def test_unordered_input_is_rejected(catalog, profiles):
    """TC-16: recognition depends on the ordering step."""
    symbols = ["GIT", "JAVASCRIPT", "REACT", "NODE_JS", "POSTGRESQL"]

    assert not accepted(profiles["FULL_STACK"], symbols, catalog), (
        "Recognition should reject an unordered sequence even when all requirements exist"
    )


def test_unfiltered_foreign_symbol_is_rejected(catalog, profiles):
    """TC-17: recognition depends on filtering foreign symbols."""
    symbols = ["DOCKER", "JAVASCRIPT", "REACT", "NODE_JS", "SQL", "GIT"]

    assert not accepted(profiles["FULL_STACK"], symbols, catalog), (
        "Recognition should reject a sequence containing an unfiltered foreign symbol"
    )


def test_empty_group_raises_value_error(catalog):
    """TC-18: an empty profile group identifies its category in the error."""
    profile = Profile("FULL_STACK", "Full Stack Developer", ("LANGUAGE", "ML_LIBRARY"))

    with pytest.raises(ValueError, match="ML_LIBRARY"):
        build_automaton(catalog, profile)
