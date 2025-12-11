# backend/pipeline/advocate.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class LetterDraft:
    letter_text: str

APPEAL_TEMPLATES = [
    {
        "id": "medical_necessity",
        "name": "Medical Necessity Appeal",
        "category": "Medical Necessity",
        "description": "Use when the insurer claims treatment is not medically necessary.",
    },
    {
        "id": "prior_auth",
        "name": "Prior Authorization Appeal",
        "category": "Prior Authorization",
        "description": "Use for denials claiming missing or invalid prior authorization.",
    },
    {
        "id": "coding_error",
        "name": "Coding Error Appeal",
        "category": "Coding Error",
        "description": "Use when denial references CPT/ICD or coding discrepancies.",
    },
    {
        "id": "administrative",
        "name": "Administrative / Other Appeal",
        "category": "Administrative",
        "description": "Use for filing deadline, missing documents, or general admin issues.",
    },
]

def generate_letter(
    template_id: str,
    denial_category: str,
    denial_reason: str,
    insurer_name: str | None,
    evidence_snippets: str,
    reasoning_summary: str,
    tone: str = "formal",
    length: str = "standard",
) -> LetterDraft:
    
    # Extract the core arguments from the reasoning summary (split from internal metrics)
    core_arguments = reasoning_summary.split("--- Internal Metrics ---")[0].strip()
    
    insurer_str = insurer_name or "Claims Department"
    
    # Professional Header (Mocking the style of the 'Actual' letter)
    header = """
LAWRENCE & ASSOCIATES PATIENT ADVOCACY
400 Legal Plaza, Metropolis, NY 10012
(212) 555-1999 | appeals@lawrence-advocacy.com

VIA CERTIFIED MAIL & FAX
""".strip()

    # Dynamic "Re:" block
    re_block = f"""
RE: URGENT APPEAL - LEVEL 1
Denial Category: {denial_category}
Insurer: {insurer_str}
Reason Referenced: "{denial_reason[:100]}..."
""".strip()

    # Tone adjustment
    intro_tone = (
        "I am writing to formally appeal the denial of coverage" 
        if tone == "formal" 
        else "I am writing to vigorously contest the invalid denial of coverage"
    )

    # Detailed Body Construction
    body = f"""
{header}

ATTN: Appeals Department
{insurer_str}

{re_block}

To the Appeals Committee:

{intro_tone} for the medically necessary services referenced above.
The denial was based on the assertion that the services were not medically necessary or lacked appropriate authorization.
This denial is invalid, clinically unsound, and inconsistent with the patient's medical history and applicable standards of care.
Please consider the following arguments:

{core_arguments}

SUPPORTING EVIDENCE SUMMARY:
{evidence_snippets or 'See attached medical records for full clinical context.'}

CONCLUSION:
The procedure was medically necessary and met the standard of care requirements.
We request that this claim be reprocessed and paid in full immediately.
Failure to rectify this error may result in further escalation to external review boards.

Sincerely,

Amanda Lawrence, Esq.
Certified Medical Appeals Specialist
Lawrence & Associates
"""

    return LetterDraft(letter_text=body.strip())

def template_options_json() -> List[Dict]:
    return APPEAL_TEMPLATES