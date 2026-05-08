"""
pdf_extractor.py
----------------
Extracts clean text + images from a PDF using PyMuPDF (fitz).

Responsibilities
================
1. Walk every page and return structured page data (page_num, text, blocks).
2. Use the PDF outline (bookmarks) when available to detect chapter / subsection
   hierarchy. Fall back to heuristic heading detection (font-size / bold / ALL CAPS).
3. Filter out Table of Contents, Index, References/Bibliography pages, page
   numbers, headers and footers using repeated-line heuristics + keyword rules.
4. Extract embedded images per page, return them as (page_num, PIL.Image) tuples.

Public API
==========
    extract_pdf(pdf_bytes_or_path)  -> dict with keys:
        - "pages":    List[{"page": int, "text": str}]
        - "outline":  List[{"title": str, "level": int, "page": int}]
        - "images":   List[{"page": int, "image": PIL.Image, "xref": int}]
        - "full_text": str (joined, cleaned)
"""

from __future__ import annotations

import io
import re
from collections import Counter
from typing import Dict, List, Tuple, Union

import fitz  # PyMuPDF
from PIL import Image

# ----------------------------- Filtering rules ------------------------------ #

# Pages whose *title/first line* matches any of these are skipped entirely.
_SKIP_PAGE_TITLES = re.compile(
    r"^\s*(table of contents|contents|index|references|bibliography|"
    r"acknowledg(e)?ments?|preface|foreword|copyright|about the author|"
    r"list of (figures|tables))\s*$",
    re.IGNORECASE,
)

# Lines that look like pure page numbers / running chapter refs.
_PAGE_NUMBER_LINE = re.compile(r"^\s*(page\s+)?\d{1,4}\s*$", re.IGNORECASE)

# Lines that look like TOC entries: "Chapter Title .......... 42"
_TOC_DOTS_LINE = re.compile(r"\.{4,}\s*\d{1,4}\s*$")


def _load_doc(source: Union[bytes, str]) -> fitz.Document:
    """Open a fitz document from bytes or file path."""
    if isinstance(source, (bytes, bytearray)):
        return fitz.open(stream=bytes(source), filetype="pdf")
    return fitz.open(source)


def _detect_repeated_headers_footers(pages_raw: List[str], threshold: float = 0.5) -> set:
    """
    Any short line (< 80 chars) that appears on >= `threshold` fraction of pages
    is treated as a running header / footer and removed from every page.
    """
    counts: Counter = Counter()
    total = max(1, len(pages_raw))
    for txt in pages_raw:
        lines = {ln.strip() for ln in txt.splitlines() if 0 < len(ln.strip()) < 80}
        for ln in lines:
            counts[ln] += 1
    return {ln for ln, c in counts.items() if c / total >= threshold}


def _clean_page_text(text: str, repeated: set) -> str:
    """Remove headers/footers, page numbers, and TOC-style dotted lines."""
    cleaned = []
    for ln in text.splitlines():
        s = ln.strip()
        if not s:
            continue
        if s in repeated:
            continue
        if _PAGE_NUMBER_LINE.match(s):
            continue
        if _TOC_DOTS_LINE.search(s):
            continue
        cleaned.append(s)
    return "\n".join(cleaned)


def _is_skippable_page(text: str) -> bool:
    """True if the page is TOC / Index / References-style meta content."""
    first_nonempty = next((ln.strip() for ln in text.splitlines() if ln.strip()), "")
    if _SKIP_PAGE_TITLES.match(first_nonempty):
        return True
    # Heavily dotted lines = TOC page.
    dotted = sum(1 for ln in text.splitlines() if _TOC_DOTS_LINE.search(ln))
    if dotted >= 5:
        return True
    return False


def _extract_outline(doc: fitz.Document) -> List[Dict]:
    """Return bookmarks as [{title, level, page}]."""
    outline = []
    for lvl, title, page in doc.get_toc(simple=True) or []:
        outline.append({"title": title.strip(), "level": lvl, "page": max(0, page - 1)})
    return outline


def _heuristic_headings(doc: fitz.Document) -> List[Dict]:
    """
    Fallback when no TOC: pick up likely headings by font size.
    Returns [{title, level, page}]. Level is 1 for largest, 2 for next, etc.
    """
    size_counts: Counter = Counter()
    candidates: List[Tuple[float, str, int]] = []  # (size, text, page)
    for page_idx, page in enumerate(doc):
        blocks = page.get_text("dict").get("blocks", [])
        for b in blocks:
            for line in b.get("lines", []):
                spans = line.get("spans", [])
                if not spans:
                    continue
                text = " ".join(s["text"] for s in spans).strip()
                if not text or len(text) > 120:
                    continue
                size = round(max(s["size"] for s in spans), 1)
                size_counts[size] += 1
                candidates.append((size, text, page_idx))

    if not candidates:
        return []

    # Body size = most common; anything larger is a heading.
    body_size = size_counts.most_common(1)[0][0]
    heading_sizes = sorted({s for s in size_counts if s > body_size}, reverse=True)
    size_to_level = {sz: i + 1 for i, sz in enumerate(heading_sizes[:4])}

    outline = []
    for size, text, page in candidates:
        if size in size_to_level:
            outline.append({"title": text, "level": size_to_level[size], "page": page})
    return outline


def _extract_images(doc: fitz.Document) -> List[Dict]:
    """Extract embedded raster images per page."""
    images = []
    for page_idx, page in enumerate(doc):
        for img in page.get_images(full=True):
            xref = img[0]
            try:
                base = doc.extract_image(xref)
                img_bytes = base["image"]
                pil = Image.open(io.BytesIO(img_bytes)).convert("RGB")
                # Skip very small decorative images (logos, bullets)
                if pil.width < 150 or pil.height < 150:
                    continue
                images.append({"page": page_idx, "image": pil, "xref": xref})
            except Exception:
                continue
    return images


def extract_pdf(source: Union[bytes, str]) -> Dict:
    """
    Main entry. Returns a dict:
        pages     -> cleaned per-page text (skippable pages removed)
        outline   -> chapter hierarchy
        images    -> embedded images
        full_text -> joined cleaned text
    """
    doc = _load_doc(source)

    # 1) Raw per-page text for repeated-line detection.
    pages_raw = [page.get_text("text") for page in doc]
    repeated = _detect_repeated_headers_footers(pages_raw)

    # 2) Clean + drop meta pages.
    pages_clean: List[Dict] = []
    for i, raw in enumerate(pages_raw):
        if _is_skippable_page(raw):
            continue
        cleaned = _clean_page_text(raw, repeated)
        if len(cleaned) < 50:  # empty / near-empty page
            continue
        pages_clean.append({"page": i, "text": cleaned})

    # 3) Outline from bookmarks first, heuristics as fallback.
    outline = _extract_outline(doc)
    if not outline:
        outline = _heuristic_headings(doc)

    # 4) Images.
    images = _extract_images(doc)

    full_text = "\n\n".join(p["text"] for p in pages_clean)

    doc.close()
    return {
        "pages": pages_clean,
        "outline": outline,
        "images": images,
        "full_text": full_text,
    }


