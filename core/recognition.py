from pyformlang.finite_automaton import DeterministicFiniteAutomaton

from core.catalog import Catalog
from core.types import ClassificationResult, OrderedQualifications
from profiles.base import Profile


def build_automaton(catalog: Catalog, profile: Profile) -> DeterministicFiniteAutomaton:
    """Build the DFA of a profile.

    For the i-th category of the profile, every qualification in its group
    moves the automaton from q(i-1) to qi, and keeps it in qi if it repeats.
    The last state is the accepting one.
    """
    automaton = DeterministicFiniteAutomaton()
    automaton.add_start_state("q0")

    for index, category in enumerate(profile.canonical_order, start=1):
        group = catalog.qualifications_for(profile.identifier, category)
        if not group:
            raise ValueError(
                f"El grupo de calificaciones para el perfil '{profile.identifier}' "
                f"y la categoría '{category}' está vacío"
            )

        previous_state = f"q{index - 1}"
        current_state = f"q{index}"
        for qualification in group:
            automaton.add_transition(previous_state, qualification, current_state)
            automaton.add_transition(current_state, qualification, current_state)

    automaton.add_final_state(f"q{len(profile.canonical_order)}")
    return automaton


def recognize(ordered: OrderedQualifications, profile: Profile, catalog: Catalog) -> ClassificationResult:
    """Classify an ordered sequence of qualifications with the profile's DFA."""
    automaton = build_automaton(catalog, profile)
    accepted = automaton.accepts(ordered.sequence)
    return ClassificationResult(profile.name, accepted)
