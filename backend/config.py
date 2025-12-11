# backend/config.py
from __future__ import annotations
from pathlib import Path

# Base project directory (backend root)
BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
CASE_DIR = DATA_DIR / "cases"
PATTERN_DIR = DATA_DIR / "patterns"
PATTERN_FILE = PATTERN_DIR / "patterns.json"
FEEDBACK_FILE = PATTERN_DIR / "feedback_log.json"

# Ensure directories exist
for d in [DATA_DIR, UPLOAD_DIR, CASE_DIR, PATTERN_DIR]:
    d.mkdir(parents=True, exist_ok=True)
