import unicodedata

def normalize_text(text: str) -> str:
    """Forma de comparación: Unicode NFKC, minúsculas y espacios colapsados.

    No elimina puntuación: ``node.js`` y ``nodejs`` son formas distintas
    (las dos quedan registradas como variantes o alias).
    """
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())
