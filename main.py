"""
Lease Document AI Tool
Author: Rasika Abhang
Date: 2025-11-08

Purpose:
Extract comprehensive insights from uploaded lease agreements — including rent,
deposit, parties, property, insurance, fees, and clause details — using rule-based
pattern recognition and text parsing.
"""

from fastapi import FastAPI
from pydantic import BaseModel
import pdfplumber
import os
import re

app = FastAPI(title="Smart Lease Info Extractor")


class LeaseFileRequest(BaseModel):
    file_path: str


@app.post("/api/ai/process-lease")
async def process_lease_file(request: LeaseFileRequest):
    """Extract structured lease details from uploaded PDF."""
    pdf_path = request.file_path

    if not os.path.isfile(pdf_path):
        return {"error": "PDF file not found at the given path."}

    # Step 1 – Read PDF content
    lease_text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    lease_text += text + "\n"
    except Exception as e:
        return {"error": f"Failed to read PDF: {str(e)}"}

    print("\n🔍 Extracting from:", pdf_path)
    print(lease_text[:400], "\n----------------------------\n")

    # Helper function for regex matching
    def match_any(patterns, text):
        for pattern in patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                return m.group(1)
        return None

    # --- Financial Details ---
    rent = match_any([
        r"base\s*rent[^$]{0,20}\$\s?([\d,]+(?:\.\d{2})?)",
        r"monthly\s*rent[^$]{0,20}\$\s?([\d,]+(?:\.\d{2})?)",
        r"rent\s*amount[^$]{0,20}\$\s?([\d,]+(?:\.\d{2})?)"
    ], lease_text)

    deposit = match_any([
        r"security\s*deposit[^$]{0,30}\$\s?([\d,]+(?:\.\d{2})?)"
    ], lease_text)
    if "not required to pay a security deposit" in lease_text.lower():
        deposit = "0.00"

    pet_fee = match_any([
        r"pet\s*(?:fee|deposit|charge)[^$]{0,20}\$\s?([\d,]+(?:\.\d{2})?)"
    ], lease_text)
    if re.search(r"no pets|pets?.*not permitted", lease_text, re.IGNORECASE):
        pet_fee = "Not applicable"

    # --- Dates ---
    start_pattern = re.search(
        r"(?:begin|effective|from)\s+on\s+([A-Za-z]+\s*\d{1,2},?\s*\d{4})",
        lease_text, re.IGNORECASE
    )
    end_pattern = re.search(
        r"(?:end|until|to)\s+on\s+([A-Za-z]+\s*\d{1,2},?\s*\d{4})",
        lease_text, re.IGNORECASE
    )

    # --- Parties (Landlord & Tenant) ---
    landlord = match_any([
        r"([A-Z][a-z]+(?:\s[A-Z][a-z]+){1,3})\s*\(Landlord\)",
        r"Landlord[:\s-]+([A-Z][a-z]+(?:\s[A-Z][a-z]+){1,3})"
    ], lease_text)

    tenant_block = re.search(
        r"([A-Z][a-z]+(?:\s[A-Z][a-z]+)?(?:\s*(?:and|,)\s*[A-Z][a-z]+(?:\s[A-Z][a-z]+)?)*)\s*\(.*Tenant",
        lease_text
    )
    tenant = tenant_block.group(1) if tenant_block else "Not found"

    # --- Property Address ---
    address_match = re.search(
        r"for\s+(\d{3,6}\s+[A-Za-z\s]+,\s*[A-Za-z\s]+,\s*(?:TX|Texas)\s*\d{5})",
        lease_text
    )
    if not address_match:
        address_match = re.search(
            r"(\d{3,6}\s+[A-Za-z\s]+(?:Dr|Street|Ave|Road|Ln|Ct)[\s,]+[A-Za-z\s]+,\s*(?:TX|Texas)\s*\d{5})",
            lease_text
        )
    address = address_match.group(1) if address_match else "Not found"

    # --- Fees and Clauses ---
    late_fee = match_any([
        r"late\s*fee[^$]{0,20}\$\s?([\d,]+(?:\.\d{2})?)"
    ], lease_text)

    nsf_fee = match_any([
        r"insufficient\s*funds\s*fee[^$]{0,20}\$\s?([\d,]+(?:\.\d{2})?)",
        r"nsf\s*fee[^$]{0,20}\$\s?([\d,]+(?:\.\d{2})?)"
    ], lease_text)

    insurance_required = not bool(
        re.search(r"not required to maintain renter.?s insurance", lease_text, re.IGNORECASE)
    )
    eviction_clause = bool(
        re.search(r"evict|eviction|default|termination notice", lease_text, re.IGNORECASE)
    )

    # --- Confidence ---
    confidence = sum([
        bool(rent),
        bool(deposit),
        bool(start_pattern),
        bool(end_pattern)
    ]) / 4

    # --- Structured Response ---
    details = {
        "Property Address": address if address else "Not found",
        "Landlord Name": landlord if landlord else "Not found",
        "Tenant Name(s)": tenant if tenant else "Not found",
        "Rent Amount": f"${rent}" if rent else "Not found",
        "Security Deposit": f"${deposit}" if deposit else "Not found",
        "Pet Fee": f"${pet_fee}" if pet_fee else "Not found",
        "Lease Start Date": start_pattern.group(1) if start_pattern else "Not found",
        "Lease End Date": end_pattern.group(1) if end_pattern else "Not found",
        "Late Fee": f"${late_fee}" if late_fee else "Not found",
        "NSF Fee": f"${nsf_fee}" if nsf_fee else "Not found",
        "Insurance Required": insurance_required,
        "Eviction Clause Present": eviction_clause,
        "Extraction Confidence": f"{confidence * 100:.0f}%",
        "Lease Text Preview": lease_text[:400] + "..."
    }

    # --- Clean up line breaks ---
    for k, v in details.items():
        if isinstance(v, str):
            details[k] = v.replace("\n", " ").strip()

    return {"lease_details": details}


