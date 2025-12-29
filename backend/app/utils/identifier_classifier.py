"""
V4 Identifier Classifier
Classifies and normalizes company identifiers for SK, CZ, PL, HU.
With confidence scoring and fallback candidates.
"""
import re
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any


@dataclass
class IdClassification:
    raw: str
    normalized: str
    digits: str
    country: Optional[str]          # "SK" | "CZ" | "PL" | "HU" | None
    id_type: str                    # "VAT" | "ICO" | "DIC" | "NIP" | "KRS" | "REGON" | "ADOSZAM" | "CEGJEGYZEKSZAM" | "UNKNOWN"
    confidence: float               # 0..1
    candidates: List[Dict[str, Any]]  # fallback possibilities (country+id_type)
    formatted: Dict[str, str]       # nice-to-have canonical formatting


def _digits_only(s: str) -> str:
    return re.sub(r"\D+", "", s)


def _normalize(s: str) -> str:
    # remove spaces, tabs, NBSP; uppercase; keep dashes for HU patterns
    s = s.strip().upper()
    s = re.sub(r"[\s\u00A0]+", "", s)
    return s


def pl_nip_checksum_ok(nip10: str) -> bool:
    """
    PL NIP checksum:
    weights: 6,5,7,2,3,4,5,6,7
    checksum = (sum(d[i]*w[i]) % 11), must equal last digit, and checksum != 10
    """
    if not re.fullmatch(r"\d{10}", nip10):
        return False
    weights = [6, 5, 7, 2, 3, 4, 5, 6, 7]
    s = sum(int(nip10[i]) * weights[i] for i in range(9))
    chk = s % 11
    if chk == 10:
        return False
    return chk == int(nip10[9])


def classify_identifier(value: str, country_hint: Optional[str] = None) -> IdClassification:
    raw = value
    s = _normalize(value)
    digits = _digits_only(s)

    candidates: List[Dict[str, Any]] = []
    formatted: Dict[str, str] = {}

    hint = country_hint.upper() if country_hint else None

    # --- Prefix VAT first (most deterministic) ---
    if re.fullmatch(r"SK\d{10}", s):
        return IdClassification(raw, s, digits, "SK", "VAT", 1.0, [], {"vat": s})

    if re.fullmatch(r"CZ\d{8,10}", s):
        return IdClassification(raw, s, digits, "CZ", "VAT", 1.0, [], {"vat": s})

    if re.fullmatch(r"PL\d{10}", s):
        return IdClassification(raw, s, digits, "PL", "VAT", 1.0, [], {"vat": s})

    # --- HU: Adószám & Cégjegyzékszám (explicit patterns) ---
    if re.fullmatch(r"\d{8}-\d-\d{2}", s):
        formatted["adoszam"] = s
        formatted["adoszam_digits"] = digits
        return IdClassification(raw, s, digits, "HU", "ADOSZAM", 1.0, [], formatted)

    if re.fullmatch(r"\d{2}-\d{2}-\d{6}", s):
        formatted["cegjegyzekszam"] = s
        formatted["cegjegyzekszam_digits"] = digits
        return IdClassification(raw, s, digits, "HU", "CEGJEGYZEKSZAM", 1.0, [], formatted)

    # HU Adószám digits-only (11 digits). Risk of collision is low.
    if re.fullmatch(r"\d{11}", digits):
        # canonical 8-1-2 formatting
        formatted["adoszam_digits"] = digits
        formatted["adoszam"] = f"{digits[:8]}-{digits[8]}-{digits[9:]}"
        # If hint exists and is NOT HU, lower confidence and keep as candidate
        if hint and hint != "HU":
            candidates.append({"country": "HU", "id_type": "ADOSZAM", "confidence": 0.55})
            return IdClassification(raw, s, digits, hint, "UNKNOWN", 0.35, candidates, formatted)
        return IdClassification(raw, s, digits, "HU", "ADOSZAM", 0.9, [], formatted)

    # --- Pure digits classification ---
    if re.fullmatch(r"\d{8}", digits):
        # SK/CZ IČO collision -> return ambiguous with candidates
        formatted["ico"] = digits
        candidates = [
            {"country": "SK", "id_type": "ICO", "confidence": 0.5},
            {"country": "CZ", "id_type": "ICO", "confidence": 0.5},
        ]
        # If hint given, bias it
        if hint in ("SK", "CZ"):
            for c in candidates:
                if c["country"] == hint:
                    c["confidence"] = 0.8
                else:
                    c["confidence"] = 0.2
            return IdClassification(raw, s, digits, hint, "ICO", 0.7, candidates, formatted)

        return IdClassification(raw, s, digits, None, "ICO", 0.55, candidates, formatted)

    if re.fullmatch(r"\d{9}", digits) or re.fullmatch(r"\d{14}", digits):
        formatted["regon"] = digits
        return IdClassification(raw, s, digits, "PL", "REGON", 0.95, [], formatted)

    if re.fullmatch(r"\d{10}", digits):
        # Could be: PL NIP, PL KRS, SK DIČ, HU cegjegyzekszam (digits-only) – but HU ceg is safer when user included separators.
        formatted["ten_digits"] = digits

        # If hint strongly indicates SK
        if hint == "SK":
            candidates = [
                {"country": "SK", "id_type": "DIC", "confidence": 0.75},
                {"country": "PL", "id_type": "NIP", "confidence": 0.20},
                {"country": "PL", "id_type": "KRS", "confidence": 0.05},
            ]
            return IdClassification(raw, s, digits, "SK", "DIC", 0.7, candidates, formatted)

        # If hint strongly indicates PL
        if hint == "PL":
            if pl_nip_checksum_ok(digits):
                return IdClassification(raw, s, digits, "PL", "NIP", 0.9, [], {"nip": digits, "vat": f"PL{digits}"})
            candidates = [
                {"country": "PL", "id_type": "KRS", "confidence": 0.65},
                {"country": "PL", "id_type": "NIP", "confidence": 0.25},
                {"country": "SK", "id_type": "DIC", "confidence": 0.10},
            ]
            return IdClassification(raw, s, digits, "PL", "KRS", 0.65, candidates, formatted)

        # No hint: use checksum to prefer NIP if valid, else KRS/SK DIC
        if pl_nip_checksum_ok(digits):
            return IdClassification(raw, s, digits, "PL", "NIP", 0.85, [], {"nip": digits, "vat": f"PL{digits}"})

        candidates = [
            {"country": "PL", "id_type": "KRS", "confidence": 0.50},
            {"country": "SK", "id_type": "DIC", "confidence": 0.35},
            {"country": "PL", "id_type": "NIP", "confidence": 0.15},
        ]
        return IdClassification(raw, s, digits, None, "UNKNOWN", 0.45, candidates, formatted)

    return IdClassification(raw, s, digits, None, "UNKNOWN", 0.0, [], {})


# Quick demo:
if __name__ == "__main__":
    tests = [
        "SK2020123456",
        "CZ12345678",
        "14906428-2-06",
        "01-09-562739",
        "00686930",
        "1234567890",
        "PL1234567890",
        "123456789",
        "12345678901234",
    ]
    for t in tests:
        print(asdict(classify_identifier(t)))
