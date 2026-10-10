
from __future__ import annotations

from core.catalog import Catalog
from core.types import NormalizedQualifications


class OrderingError(ValueError):
    """Error al ordenar calificaciones según un perfil profesional."""


# El orden de las categorías es independiente del JSON.
_CATEGORY_ORDER = (
    "LANGUAGE",
    "FRONTEND",
    "BACKEND",
    "DATABASE",
    "ML_LIBRARY",
    "DATA_PROCESSING",
    "WORKFLOW",
    "CONTAINER",
    "CI_CD",
    "IAC",
    "CLOUD",
    "VCS",
)


def order(
    normalized: NormalizedQualifications,
    profile: str,
    catalog: Catalog,
) -> list[str]:
    """Filtra y ordena las calificaciones canónicas según un perfil."""

    valid_profiles = {
        valid_profile
        for qualification in catalog
        for valid_profile in qualification.profiles
    }

    if profile not in valid_profiles:
        raise OrderingError(
            f"Perfil no válido: '{profile}'. "
            f"Perfiles admitidos: {', '.join(sorted(valid_profiles))}."
        )

    # Validar todas las calificaciones antes de filtrar por perfil.
    for canonical in normalized.tokens:
        try:
            catalog.get(canonical)
        except KeyError:
            raise OrderingError(
                "Calificación canónica no encontrada en el catálogo: "
                f"'{canonical}'."
            ) from None

    # Eliminar duplicados sin modificar la entrada.
    unique_tokens = set(normalized.tokens)

    # Filtrar las calificaciones que pertenecen al perfil.
    eligible_tokens = {
        canonical
        for canonical in unique_tokens
        if profile in catalog.get(canonical).profiles
    }

    # Orden fijo de categorías y posición original dentro de cada categoría.
    category_priority = {
        category: index
        for index, category in enumerate(_CATEGORY_ORDER)
    }

    return sorted(
        eligible_tokens,
        key=lambda canonical: (
            category_priority[catalog.category_of(canonical)],
            catalog.position(canonical),
        ),
    )
