from profiles.base import Profile

DATA_ENGINEER = Profile(
    identifier="DATA_ENGINEER",
    name="Data Engineer",
    canonical_order=(
        "LANGUAGE",
        "DATABASE",
        "DATA_PROCESSING",
        "WORKFLOW",
        "CLOUD",
        "VCS",
    ),
)
