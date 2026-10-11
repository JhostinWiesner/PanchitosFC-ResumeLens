from core.catalog import Catalog
from core.types import NormalizedQualifications, OrderedQualifications
from profiles.base import Profile


def order(normalized: NormalizedQualifications, profile: Profile, catalog: Catalog,) -> OrderedQualifications:
    """Keep the qualifications of the profile and sort them by its category order."""
    priority = {category: i for i, category in enumerate(profile.canonical_order)}

    eligible = {
        canonical
        for canonical in normalized.tokens
        if profile.identifier in catalog.get(canonical).profiles
        and catalog.category_of(canonical) in priority
    }

    sequence = sorted(
        eligible,
        key=lambda c: (priority[catalog.category_of(c)], catalog.position(c)),
    )
    return OrderedQualifications(profile.name, sequence)
