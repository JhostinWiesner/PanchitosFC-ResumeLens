
from __future__ import annotations

from pyformlang.fst import FST

from core.catalog import Catalog
from core.text import normalize_text
from core.types import ExtractedData, NormalizedQualifications


_END_MARKER = "#"


def _build_transducer(spellings: dict[str, str]) -> FST:
    """Build one FST using a trie shared by all catalog spellings."""
    nodes: list[dict] = [{"children": {}, "canonical": None}]

    # Build a trie so common prefixes share states.
    for spelling, canonical in spellings.items():
        state = 0

        for char in spelling:
            children = nodes[state]["children"]

            if char not in children:
                children[char] = len(nodes)
                nodes.append({"children": {}, "canonical": None})

            state = children[char]

        nodes[state]["canonical"] = canonical

    fst = FST()
    fst.add_start_state(0)

    for state, node in enumerate(nodes):
        for char, destination in node["children"].items():
            fst.add_transition(state, char, destination, [])

        canonical = node["canonical"]
        if canonical is not None:
            final_state = f"final_{state}"
            fst.add_transition(
                state,
                _END_MARKER,
                final_state,
                [canonical],
            )
            fst.add_final_state(final_state)

    return fst


def normalize(extracted: ExtractedData) -> NormalizedQualifications:
    """Normalize extracted skill candidates into canonical qualifications."""
    catalog = Catalog.from_json()
    spellings = catalog.spellings()
    fst = _build_transducer(spellings)

    tokens: list[str] = []
    unrecognized: list[str] = []

    for raw in extracted.skills_raw:
        normalized = normalize_text(raw)

        # Ignore blank candidates rather than reporting them as skills.
        if not normalized:
            continue

        # The marker tells the FST that this candidate has ended.
        input_symbols = list(normalized + _END_MARKER)
        outputs = list(fst.translate(input_symbols))

        if len(outputs) == 1 and len(outputs[0]) == 1:
            tokens.append(outputs[0][0])
        else:
            # Preserve the original text for diagnostics.
            unrecognized.append(raw)

    return NormalizedQualifications(
        tokens=tokens,
        unrecognized=unrecognized,
    )
