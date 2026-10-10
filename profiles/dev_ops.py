from profiles.base import Profile

DEVOPS = Profile(
    identifier="DEVOPS",
    name="DevOps Engineer",
    canonical_order=(
        "LANGUAGE",
        "CONTAINER",
        "CI_CD",
        "IAC",
        "CLOUD",
        "VCS",
    ),
)
