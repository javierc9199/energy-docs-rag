"""Lightweight Spanish text utilities used by the abstention gate."""

from __future__ import annotations

import re
import unicodedata

# Function words and question words that carry no topical content.
STOPWORDS = frozenset(
    """
    a al algo algunas algunos ante antes como con contra cual cuales cuando de del desde
    donde dos el ella ellas ellos en entre era es esa esas ese eso esos esta estas este
    esto estos fue ha hace hay la las le les lo los mas me mi mientras muy mucho nada ni
    no nos o otra otras otro otros para pero poco por porque que se sea segun ser si sin
    sobre son su sus tambien tan tanto te tiene tienen todo todos tu un una unas uno unos
    y ya cuanto cuanta cuantos cuantas hacer hago puede pueden debe deben cada
    quien quienes habia habian hubo dice dicen hace hacen tenia tener estan estaba
    """.split()
)

_WORD = re.compile(r"[a-z0-9]+")


def normalise(text: str) -> str:
    """Lowercase and strip accents, so "Tensión" and "tension" match."""
    return unicodedata.normalize("NFKD", text.lower()).encode("ascii", "ignore").decode()


def stem(word: str) -> str:
    """Crude plural folding ("seguidores" -> "seguidor"); enough for a coverage signal."""
    for suffix in ("es", "s"):
        if len(word) > 4 and word.endswith(suffix):
            return word[: -len(suffix)]
    return word


def content_terms(text: str) -> list[str]:
    return [stem(w) for w in _WORD.findall(normalise(text)) if w not in STOPWORDS and len(w) > 2]


def coverage(question: str, vocabulary: set[str]) -> float:
    """Fraction of the question's content terms that appear anywhere in the corpus."""
    terms = content_terms(question)
    if not terms:
        return 0.0
    return sum(term in vocabulary for term in terms) / len(terms)
