import re

def test_split(address_text):
    data = {"address": address_text, "zip": None, "street": None, "city": None}
    postal_match = re.search(r"(\b\d{5}\b|\b\d{3}\s\d{2}\b)", address_text)
    if postal_match:
        postal_code = postal_match.group()
        data["zip"] = postal_code
        parts = address_text.split(postal_code)
        if len(parts) >= 2:
            before_zip = parts[0].strip().rstrip(",")
            print(f"Before ZIP: '{before_zip}'")
            match_street_city = re.search(r"^(.*?)\s+([^\s\d]+(?: [^\s\d]+)*)$", before_zip)
            if match_street_city:
                data["street"] = match_street_city.group(1).strip().rstrip(",")
                data["city"] = match_street_city.group(2).strip()
            else:
                data["street"] = before_zip
                data["city"] = before_zip
        elif len(parts) == 1:
            data["street"] = parts[0].strip()
    return data

print(test_split("Čadečka 541 Čadca 022 01"))
