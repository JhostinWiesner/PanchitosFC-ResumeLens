from dataclasses import dataclass

ACCEPTED_TEXT = "The normalized qualifications satisfy an accepted {profile} pattern."
REJECTED_TEXT = "The normalized qualifications do not satisfy an accepted {profile} pattern."

@dataclass(frozen=True)
class Profile:
    """A professional profile. It only holds data.

    identifier:      id used in catalog.json (e.g. "FULL_STACK")
    name:            display name (e.g. "Full Stack Developer")
    canonical_order: categories in the order the profile requires
    """

    identifier: str
    name: str
    canonical_order: tuple[str, ...]

    def get_explanation(self, accepted: bool) -> str:
        template = ACCEPTED_TEXT if accepted else REJECTED_TEXT
        return template.format(profile=self.name)