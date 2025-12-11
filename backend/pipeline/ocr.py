# backend/pipeline/ocr.py
from __future__ import annotations
from pathlib import Path

import pdfplumber
from PIL import Image
import pytesseract

def extract_text_from_file(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _extract_text_from_pdf(path)
    if suffix in [".png", ".jpg", ".jpeg", ".bmp", ".tiff"]:
        return _extract_text_from_image(path)

    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""

def _extract_text_from_pdf(path: Path) -> str:
    text_chunks = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text_chunks.append(pdf.pages.index(page) * "\n")  # just a separator
            text_chunks.append(page.extract_text() or "")
    return "\n".join(text_chunks)

def _extract_text_from_image(path: Path) -> str:
    img = Image.open(path)
    return pytesseract.image_to_string(img)

def normalize_text(raw: str) -> str:
    import re
    text = raw.replace("\r", "\n")
    text = re.sub(r"[^\S\n]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
