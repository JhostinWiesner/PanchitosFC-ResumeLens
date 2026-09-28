from abc import ABC, abstractmethod
from pyformlang.finite_automaton import FiniteAutomaton


class Profile(ABC):
    """Base abstract class for professional profiles."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the profile (e.g., 'Full Stack Developer')."""
        pass

    @property
    @abstractmethod
    def canonical_order(self) -> list[str]:
        """Ordered list of canonical qualifications for this profile."""
        pass

    @property
    @abstractmethod
    def automaton(self) -> FiniteAutomaton:
        """Automaton that accepts the canonical order of qualifications for this profile."""
        pass

    @abstractmethod
    def get_explanation(self, accepted: bool) -> str:
        """Generates an explanation for the classification result based on whether the profile was accepted or rejected."""
        pass