"""
summarizer.py
-------------
Local, offline extractive summarization.

Strategy
========
- Use sumy's LexRank for fast extractive summaries (no LLM required).
- Post-process sentences into short, student-friendly bullet points.
- Provide two entry points:
    summarize_text(text, max_bullets)       -> List[str]
    summarize_sections(grouped_chunks, ...) -> Dict[section, List[str]]
"""

from __future__ import annotations

import re
from typing import Dict, List

import nltk
from sumy.nlp.tokenizers import Tokenizer
from sumy.parsers.plaintext import PlaintextParser
from sumy.summarizers.lex_rank import LexRankSummarizer


# Ensure required NLTK data is available on first use (safe to call repeatedly).
def _ensure_nltk() -> None:
    for pkg in ("punkt", "punkt_tab"):
        try:
            nltk.data.find(f"tokenizers/{pkg}")
        except LookupError:
            try:
                nltk.download(pkg, quiet=True)
            except Exception:
                pass


_SPACE_RE = re.compile(r"\s+")


def _clean_sentence(s: str) -> str:
    s = _SPACE_RE.sub(" ", s).strip()
    # Strip leading numbering / bullets
    s = re.sub(r"^[\-\u2022\*\d\.\)\(]+\s*", "", s)
    # Capitalize first letter
    if s and s[0].islower():
        s = s[0].upper() + s[1:]
    # Ensure period
    if s and s[-1] not in ".!?":
        s += "."
    return s


def _shorten(sentence: str, max_words: int = 22) -> str:
    """Keep bullets classroom-friendly: cap length."""
    words = sentence.split()
    if len(words) <= max_words:
        return sentence
    short = " ".join(words[:max_words]).rstrip(",;:") + "…"
    return short


def summarize_text(text: str, max_bullets: int = 5) -> List[str]:
    """Return up to `max_bullets` clean, short bullet sentences."""
    _ensure_nltk()
    text = text.strip()
    if not text:
        return []

    try:
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = LexRankSummarizer()
        sentences = summarizer(parser.document, max_bullets * 2)
        raw = [str(s) for s in sentences]
    except Exception:
        # Fallback: split by sentence and take the first N
        raw = re.split(r"(?<=[.!?])\s+", text)

    seen, bullets = set(), []
    for s in raw:
        cleaned = _clean_sentence(s)
        if len(cleaned.split()) < 4:
            continue
        key = cleaned.lower()[:80]
        if key in seen:
            continue
        seen.add(key)
        bullets.append(_shorten(cleaned))
        if len(bullets) >= max_bullets:
            break
    return bullets


def summarize_sections(
    grouped_chunks: Dict[str, List[Dict]],
    bullets_per_section: int = 5,
) -> Dict[str, List[str]]:
    """
    Takes {section_title: [chunk, chunk, ...]} from RAGRetriever.retrieve_by_section
    and returns {section_title: [bullet, bullet, ...]}.
    """
    out: Dict[str, List[str]] = {}
    for section, chunks in grouped_chunks.items():
        text = " ".join(c["text"] for c in chunks)
        bullets = summarize_text(text, max_bullets=bullets_per_section)
        if bullets:
            out[section] = bullets
    return out


def build_intro(topic: str, all_bullets: List[str]) -> List[str]:
    """Create a short introduction for slide 1 using top-level bullets."""
    lead = [
        f"This presentation covers the topic: {topic}.",
        "We will explore its key concepts, subtopics, and practical examples.",
    ]
    # Add up to 2 supporting bullets from the overall content
    for b in all_bullets[:2]:
        lead.append(b)
    return lead[:4]


def build_conclusion(topic: str, section_bullets: Dict[str, List[str]]) -> List[str]:
    """Synthesize a closing slide from the first bullet of each section."""
    points = [
        f"{topic} is a rich area with several interconnected ideas.",
    ]
    for section, bullets in list(section_bullets.items())[:4]:
        if bullets:
            points.append(f"{section}: {bullets[0]}")
    points.append("Review the subtopics above to build a complete understanding.")
    return points


