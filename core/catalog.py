from __future__ import annotations

from text import normalize_text

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

DEFAULT_CATALOG_PATH = Path(__file__).with_name("catalog.json")

_NAME_RE = re.compile(r"[A-Z0-9]+(?:_[A-Z0-9]+)*")
_JOINERS = (" ", "-", ".", "", "_")  # cómo se pueden unir las palabras de un nombre


class CatalogError(ValueError):
    """El archivo del catálogo es inválido o inconsistente."""

def name_variants(canonical: str) -> tuple[str, ...]:
    """Variantes automáticas de un nombre canónico (opción A).

    ``SCIKIT_LEARN`` -> ``scikit learn``, ``scikit-learn``, ``scikit.learn``,
    ``scikitlearn``, ``scikit_learn``. Un nombre de una sola palabra
    (``PYTHON``) produce solo ``python``.
    """
    words = canonical.split("_")
    forms: list[str] = []
    for joiner in _JOINERS:
        form = normalize_text(joiner.join(words))
        if form not in forms:
            forms.append(form)
    return tuple(forms)


@dataclass(frozen=True)
class Qualification:
    """Una tecnología del catálogo.

    ``position`` es el índice global en el JSON: dentro de una categoría
    conserva el orden de las filas y sirve de desempate en ``order()``.
    """

    canonical: str
    category: str
    aliases: tuple[str, ...]
    position: int
    spellings: tuple[str, ...]  # alias + variantes del canónico, ya normalizados


class Catalog:
    """Catálogo validado e indexado."""

    def __init__(self, qualifications: tuple[Qualification, ...]) -> None:
        self._items = qualifications
        self._by_canonical = {q.canonical: q for q in qualifications}
        self._by_spelling: dict[str, str] = {}
        for q in qualifications:
            for form in q.spellings:
                owner = self._by_spelling.get(form)
                if owner is not None and owner != q.canonical:
                    raise CatalogError(
                        f"El texto '{form}' apunta a dos calificaciones: "
                        f"{owner} y {q.canonical}"
                    )
                self._by_spelling[form] = q.canonical

    # ---- construcción -------------------------------------------------
    @classmethod
    def from_json(cls, path: str | Path = DEFAULT_CATALOG_PATH) -> "Catalog":
        path = Path(path)
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise CatalogError(f"No existe el catálogo: {path}") from exc
        except json.JSONDecodeError as exc:
            raise CatalogError(f"JSON inválido en {path}: {exc}") from exc
        return cls.from_dict(raw)

    @classmethod
    def from_dict(cls, raw: object) -> "Catalog":
        if not isinstance(raw, dict) or not isinstance(raw.get("qualifications"), list):
            raise CatalogError("El catálogo debe ser un objeto con la lista 'qualifications'")

        items: list[Qualification] = []
        seen: set[str] = set()
        for position, entry in enumerate(raw["qualifications"]):
            where = f"qualifications[{position}]"
            if not isinstance(entry, dict):
                raise CatalogError(f"{where}: debe ser un objeto")
            missing = {"canonical", "category", "aliases"} - entry.keys()
            if missing:
                raise CatalogError(f"{where}: faltan campos {sorted(missing)}")

            canonical, category, aliases = entry["canonical"], entry["category"], entry["aliases"]
            for label, value in (("canonical", canonical), ("category", category)):
                if not isinstance(value, str) or not _NAME_RE.fullmatch(value):
                    raise CatalogError(
                        f"{where}: '{label}' debe ser MAYUSCULAS_CON_GUION_BAJO, recibido {value!r}"
                    )
            if not isinstance(aliases, list) or not all(
                    isinstance(a, str) and a.strip() for a in aliases
            ):
                raise CatalogError(f"{where}: 'aliases' debe ser una lista de textos no vacíos")
            if canonical in seen:
                raise CatalogError(f"{where}: canónico repetido '{canonical}'")
            seen.add(canonical)

            forms: list[str] = []
            for text in (*aliases, *name_variants(canonical)):
                form = normalize_text(text)
                if form not in forms:
                    forms.append(form)
            items.append(
                Qualification(canonical, category, tuple(aliases), position, tuple(forms))
            )
        return cls(tuple(items))

    def get(self, canonical: str) -> Qualification:
        try:
            return self._by_canonical[canonical]
        except KeyError:
            raise KeyError(f"'{canonical}' no es un nombre canónico del catálogo") from None

    def category_of(self, canonical: str) -> str:
        return self.get(canonical).category

    def position(self, canonical: str) -> int:
        """Posición global: desempate dentro de una categoría en ``order()``."""
        return self.get(canonical).position

    @property
    def categories(self) -> tuple[str, ...]:
        """Categorías en orden de primera aparición en el JSON."""
        return tuple(dict.fromkeys(q.category for q in self._items))

    def spellings(self) -> dict[str, str]:
        """Todos los textos reconocidos (normalizados) -> canónico. Insumo del FST."""
        return dict(self._by_spelling)

    def __iter__(self) -> Iterator[Qualification]:
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def __contains__(self, canonical: object) -> bool:
        return canonical in self._by_canonical
