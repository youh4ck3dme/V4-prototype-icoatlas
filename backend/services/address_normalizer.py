import re
from typing import Dict, Optional


def normalize_address(raw_address: str) -> Dict[str, Optional[str]]:
    """Very simple address normalizer for Slovak ORSR address strings.
    Expected format (example):
        "Hodžovo námestie 3 Bratislava 1 811 06"
    Returns a dict with keys: street, city, city_part, postal_code.
    The implementation uses a heuristic based on the last three tokens being
    city_part, postal_code (two parts). It works for the typical ORSR format.
    """
    if not raw_address:
        return {"street": None, "city": None, "city_part": None, "postal_code": None}

    parts = raw_address.split()
    # Postal code is usually two parts: 3 digits and 2 digits (e.g., 811 06)
    if len(parts) >= 3 and re.fullmatch(r"\d{3}", parts[-2]) and re.fullmatch(r"\d{2}", parts[-1]):
        postal_code = f"{parts[-2]} {parts[-1]}"
        # The token before postal code is the city part number (e.g., "1")
        city_part_number = parts[-3]
        city = parts[-4] if len(parts) >= 4 else None
        city_part = f"{city} {city_part_number}" if city else city_part_number
        street = " ".join(parts[:-4]) if len(parts) > 4 else None
    else:
        # Fallback: treat everything before last token as street, last token as city
        postal_code = None
        city = parts[-1] if parts else None
        street = " ".join(parts[:-1]) if len(parts) > 1 else None
        city_part = None

    return {
        "street": street,
        "city": city,
        "city_part": city_part,
        "postal_code": postal_code,
    }
