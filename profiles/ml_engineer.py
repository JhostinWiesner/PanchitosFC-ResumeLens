from profiles.base import Profile

ML_ENGINEER = Profile(
    identifier="ML_ENGINEER",
    name="Machine Learning Engineer",
    canonical_order=(
        "LANGUAGE",
        "DATABASE",
        "ML_LIBRARY",
        "VCS",
    ),
)
