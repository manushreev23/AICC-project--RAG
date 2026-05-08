"""
image_handler.py
----------------
Image sourcing for slides.

Order of preference:
1. Images already extracted from the PDF (pdf_extractor.extract_pdf -> images).
2. Unsplash (keyless) via https://source.unsplash.com/featured/?<query>
   Falls back to loremflickr.com if Unsplash is unreachable.

All images are returned as local file paths (png) for python-pptx insertion.
"""

from __future__ import annotations

import hashlib
import io
import os
import re
from typing import Dict, List, Optional

import requests
from PIL import Image


# Cache directory for downloaded / saved images (per run).
CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "output", "_img_cache")
os.makedirs(CACHE_DIR, exist_ok=True)


def _save_pil(img: Image.Image, key: str) -> str:
    """Persist a PIL image to disk and return the path."""
    safe = hashlib.md5(key.encode("utf-8")).hexdigest()[:12]
    path = os.path.join(CACHE_DIR, f"{safe}.png")
    img.convert("RGB").save(path, "PNG", optimize=True)
    return path


def save_pdf_images(images: List[Dict]) -> List[Dict]:
    """
    Convert in-memory PIL images (from pdf_extractor) to on-disk paths.
    Returns list of {"page": int, "path": str}.
    """
    out = []
    for i, item in enumerate(images):
        try:
            path = _save_pil(item["image"], f"pdf_{item.get('page', 0)}_{i}")
            out.append({"page": item.get("page", 0), "path": path})
        except Exception:
            continue
    return out


def pick_pdf_image_for_section(
    pdf_images: List[Dict], section_page_range: Optional[range] = None
) -> Optional[str]:
    """Pick the first PDF image whose page lies in the section's page range."""
    if not pdf_images:
        return None
    if section_page_range is None:
        return pdf_images[0]["path"]
    for img in pdf_images:
        if img["page"] in section_page_range:
            return img["path"]
    return pdf_images[0]["path"]


# ------------------------- Web fallback (Unsplash) -------------------------- #

_UA = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}


def _clean_query(q: str) -> str:
    q = re.sub(r"[^A-Za-z0-9\s]", " ", q)
    q = re.sub(r"\s+", " ", q).strip()
    return q or "education"


def fetch_unsplash_image(query: str, width: int = 1200, height: int = 800) -> Optional[str]:
    """
    Keyless Unsplash via source.unsplash.com. Returns local PNG path or None.
    """
    q = _clean_query(query).replace(" ", ",")
    urls = [
        f"https://source.unsplash.com/featured/{width}x{height}/?{q}",
        f"https://loremflickr.com/{width}/{height}/{q.replace(',', '%20')}",
    ]
    for url in urls:
        try:
            r = requests.get(url, headers=_UA, timeout=12, allow_redirects=True)
            if r.status_code == 200 and r.content and len(r.content) > 2048:
                img = Image.open(io.BytesIO(r.content)).convert("RGB")
                return _save_pil(img, f"web_{query}_{url}")
        except Exception:
            continue
    return None


def get_image_for_slide(
    slide_query: str,
    pdf_images: List[Dict],
    prefer_pdf: bool = True,
    used_paths: Optional[set] = None,
) -> Optional[str]:
    """
    Resolve an image for a slide: PDF first (unused), then Unsplash fallback.
    """
    used_paths = used_paths if used_paths is not None else set()

    if prefer_pdf:
        for img in pdf_images:
            if img["path"] not in used_paths:
                used_paths.add(img["path"])
                return img["path"]

    path = fetch_unsplash_image(slide_query)
    if path:
        used_paths.add(path)
    return path

