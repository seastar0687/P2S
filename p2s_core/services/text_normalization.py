from __future__ import annotations

import re
import unicodedata


LIGATURES = {
    "\ufb00": "ff",
    "\ufb01": "fi",
    "\ufb02": "fl",
    "\ufb03": "ffi",
    "\ufb04": "ffl",
}


def normalize_text(text: str) -> str:
    """Normalize common PDF extraction artifacts while preserving paragraphs."""

    text = unicodedata.normalize("NFKC", text)
    for source, replacement in LIGATURES.items():
        text = text.replace(source, replacement)
    text = text.replace("\u00ad", "")
    text = text.replace("\u2009", " ").replace("\u00a0", " ")
    text = re.sub(r"([A-Za-z])-\s*\n\s*([a-z])", r"\1\2", text)
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def relaxed_text(text: str) -> str:
    text = normalize_text(text).lower()
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", " ", text).strip()
