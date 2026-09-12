"""
app/rag/loader.py
-----------------
Sprint 4 Step 2 — RAG Knowledge Engine

PDF text extraction and cleaning layer.

Responsibilities
----------------
- Open a PDF file from disk using ``pypdf``.
- Extract text from each page, preserving the 1-based page number.
- Clean each page's text (normalise whitespace, strip control characters).
- Skip pages that contain no meaningful text after cleaning.

Public API
----------
    from app.rag.loader import extract_pages, clean_text

    pages = extract_pages("/path/to/document.pdf")
    # [{"page_number": 1, "text": "..."}, {"page_number": 2, "text": "..."}, ...]

Design notes
------------
- ``pypdf`` is pure-Python and has no binary dependencies; it is the project's
  standard PDF library (added to requirements.txt in Sprint 4 Step 2).
- Text extraction quality depends on the PDF; scanned image-only PDFs will
  produce empty pages that are silently skipped.
- ``clean_text()`` is exposed as a public function so the chunker and tests can
  call it independently.
"""

from __future__ import annotations

import os
import re
import sys
from typing import Any

# --------------------------------------------------------------------------- #
# Project root on sys.path
# --------------------------------------------------------------------------- #
_THIS_DIR     = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_THIS_DIR))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from utils.logger import logger  # noqa: E402

try:
    from pypdf import PdfReader
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "pypdf is required for PDF text extraction. "
        "Install it with: pip install pypdf"
    ) from exc


# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

# Minimum number of non-whitespace characters for a page to be considered
# non-empty after cleaning.
MIN_PAGE_CHARS: int = 10

# Regex: any control character except tab (\x09), newline (\x0a), carriage
# return (\x0d) — those are handled by whitespace normalisation below.
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

# Regex: collapse runs of whitespace (spaces, tabs) to a single space.
_MULTI_SPACE_RE = re.compile(r"[ \t]+")

# Regex: collapse three or more consecutive newlines into exactly two.
_MULTI_NEWLINE_RE = re.compile(r"\n{3,}")


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #

def clean_text(text: str) -> str:
    """
    Clean raw text extracted from a PDF page.

    Steps applied in order
    ----------------------
    1. Strip control characters (keep \\t, \\n, \\r).
    2. Normalise horizontal whitespace (collapse spaces/tabs to one space).
    3. Collapse 3+ consecutive blank lines to a maximum of two newlines.
    4. Strip leading/trailing whitespace from the entire string.

    Parameters
    ----------
    text : str
        Raw text as returned by ``pypdf``'s ``extract_text()``.

    Returns
    -------
    str
        Cleaned text, or an empty string if *text* was None/empty.
    """
    if not text:
        return ""

    # 1. Remove control characters
    text = _CONTROL_CHARS_RE.sub("", text)

    # 2. Normalise horizontal whitespace
    text = _MULTI_SPACE_RE.sub(" ", text)

    # 3. Collapse excess blank lines
    text = _MULTI_NEWLINE_RE.sub("\n\n", text)

    # 4. Strip surrounding whitespace
    return text.strip()


def extract_pages(file_path: str) -> list[dict[str, Any]]:
    """
    Extract text from a PDF file, one dict per non-empty page.

    Parameters
    ----------
    file_path : str
        Absolute (or resolvable) path to the PDF file on disk.

    Returns
    -------
    list[dict]
        Each element is::

            {
                "page_number": <int>,   # 1-based
                "text":        <str>,   # cleaned text
            }

        Pages whose cleaned text is shorter than ``MIN_PAGE_CHARS`` characters
        are silently omitted (empty pages, image-only pages, etc.).

    Raises
    ------
    FileNotFoundError
        If *file_path* does not exist.
    ValueError
        If the file cannot be opened as a valid PDF.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"[loader] PDF not found: {file_path}")

    try:
        reader = PdfReader(file_path)
    except Exception as exc:
        raise ValueError(f"[loader] Failed to open PDF '{file_path}': {exc}") from exc

    pages: list[dict[str, Any]] = []
    total = len(reader.pages)

    for idx, page in enumerate(reader.pages):
        page_number = idx + 1  # 1-based

        try:
            raw_text = page.extract_text() or ""
        except Exception as exc:  # pragma: no cover
            logger.warning(
                f"[loader] Could not extract text from page {page_number}: {exc}"
            )
            raw_text = ""

        cleaned = clean_text(raw_text)

        if len(cleaned.replace(" ", "")) < MIN_PAGE_CHARS:
            logger.debug(
                f"[loader] Skipping empty page {page_number}/{total} in '{file_path}'"
            )
            continue

        pages.append({"page_number": page_number, "text": cleaned})

    logger.info(
        f"[loader] Extracted {len(pages)}/{total} non-empty pages from '{file_path}'"
    )
    return pages
