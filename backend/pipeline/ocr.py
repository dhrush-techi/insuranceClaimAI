# backend/pipeline/ocr.py
from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
import re

import pdfplumber
from PIL import Image
import pytesseract
import docx

@dataclass
class ProcessedPage:
    page_number: int
    text: str
    char_start: int
    char_end: int
    ocr_quality: float

@dataclass
class DocumentIngestionResult:
    document_id: str
    filename: str
    source_type: str
    full_text: str
    pages: List[ProcessedPage]
    overall_ocr_quality: float

def compute_ocr_quality(text: str) -> float:
    if not text or not text.strip():
        return 0.0
    tokens = text.split()
    if not tokens:
        return 0.0
    # Assess ratio of valid alphanumeric / readable tokens
    clean_tokens = [t for t in tokens if re.search(r"[a-zA-Z0-9]", t)]
    noise_tokens = [t for t in tokens if re.search(r"[^\w\s.,;:?!\-()/$%]", t)]
    valid_ratio = len(clean_tokens) / len(tokens)
    noise_ratio = len(noise_tokens) / len(tokens)
    
    score = max(0.0, min(1.0, valid_ratio * (1.0 - 0.5 * noise_ratio)))
    return round(score, 4)

def ingest_document(path: Path, document_id: Optional[str] = None) -> DocumentIngestionResult:
    suffix = path.suffix.lower()
    doc_id = document_id or path.stem
    pages: List[ProcessedPage] = []
    
    if suffix == ".pdf":
        pages = _extract_from_pdf(path)
        source_type = "pdf"
    elif suffix in [".docx", ".doc"]:
        pages = _extract_from_docx(path)
        source_type = "docx"
    elif suffix in [".png", ".jpg", ".jpeg", ".bmp", ".tiff"]:
        pages = _extract_from_image(path)
        source_type = "image"
    else:
        pages = _extract_from_txt(path)
        source_type = "text"

    full_text_chunks = []
    current_char_len = 0
    updated_pages = []
    
    for p in pages:
        norm_p_text = normalize_text(p.text)
        start_char = current_char_len
        end_char = start_char + len(norm_p_text)
        
        updated_pages.append(
            ProcessedPage(
                page_number=p.page_number,
                text=norm_p_text,
                char_start=start_char,
                char_end=end_char,
                ocr_quality=p.ocr_quality,
            )
        )
        full_text_chunks.append(norm_p_text)
        current_char_len = end_char + 2  # considering \n\n delimiter

    full_text = "\n\n".join(full_text_chunks)
    avg_quality = (
        round(sum(p.ocr_quality for p in updated_pages) / len(updated_pages), 4)
        if updated_pages
        else 1.0
    )

    return DocumentIngestionResult(
        document_id=doc_id,
        filename=path.name,
        source_type=source_type,
        full_text=full_text,
        pages=updated_pages,
        overall_ocr_quality=avg_quality,
    )

def extract_text_from_file(path: Path) -> str:
    res = ingest_document(path)
    return res.full_text

def _extract_from_pdf(path: Path) -> List[ProcessedPage]:
    pages = []
    try:
        with pdfplumber.open(path) as pdf:
            for idx, page in enumerate(pdf.pages, start=1):
                raw = page.extract_text() or ""
                # Fallback to OCR if page text is nearly empty
                if len(raw.strip()) < 20:
                    try:
                        p_img = page.to_image(resolution=150).original
                        raw = pytesseract.image_to_string(p_img)
                    except Exception:
                        pass
                quality = compute_ocr_quality(raw)
                pages.append(ProcessedPage(page_number=idx, text=raw, char_start=0, char_end=0, ocr_quality=quality))
    except Exception:
        pages = _extract_from_txt(path)
    return pages

def _extract_from_docx(path: Path) -> List[ProcessedPage]:
    try:
        doc = docx.Document(path)
        full_text = "\n".join([para.text for para in doc.paragraphs])
        quality = compute_ocr_quality(full_text)
        return [ProcessedPage(page_number=1, text=full_text, char_start=0, char_end=0, ocr_quality=quality)]
    except Exception:
        return _extract_from_txt(path)

def _extract_from_image(path: Path) -> List[ProcessedPage]:
    try:
        img = Image.open(path)
        raw = pytesseract.image_to_string(img)
        quality = compute_ocr_quality(raw)
        return [ProcessedPage(page_number=1, text=raw, char_start=0, char_end=0, ocr_quality=quality)]
    except Exception:
        return [ProcessedPage(page_number=1, text="", char_start=0, char_end=0, ocr_quality=0.0)]

def _extract_from_txt(path: Path) -> List[ProcessedPage]:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            raw = f.read()
        quality = compute_ocr_quality(raw)
        return [ProcessedPage(page_number=1, text=raw, char_start=0, char_end=0, ocr_quality=quality)]
    except Exception:
        return [ProcessedPage(page_number=1, text="", char_start=0, char_end=0, ocr_quality=0.0)]

def normalize_text(raw: str) -> str:
    if not raw:
        return ""
    text = raw.replace("\r", "\n")
    text = re.sub(r"[^\S\n]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
