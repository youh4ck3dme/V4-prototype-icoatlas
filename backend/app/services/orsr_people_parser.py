from bs4 import BeautifulSoup
import re
import unicodedata
import copy

def normalize_text(text):
    if not text:
        return ""
    # Replace non-breaking spaces and normalize whitespace
    text = unicodedata.normalize("NFKC", text)
    return re.sub(r'\s+', ' ', text).strip()

def normalize_label(text):
    if not text:
        return ""
    # Strip accents, lowercase, keep only alphanumeric and spaces
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = text.lower()
    return re.sub(r'[^a-z0-9\s]', '', text).strip()

def get_br_split_lines(element, decompose_links=False):
    el_copy = copy.copy(element)
    if decompose_links:
        for a in el_copy.find_all("a"):
            a.decompose()
    for br in el_copy.find_all("br"):
        br.replace_with("||BR||")
    text_content = el_copy.get_text()
    raw_lines = text_content.split("||BR||")
    
    normalized_lines = []
    for line in raw_lines:
        line_norm = normalize_text(line)
        if line_norm:
            normalized_lines.append(line_norm)
    return normalized_lines

def parse_orsr_people(html_content: str) -> dict:
    """
    Parses comprehensive data from official ORSR extract HTML.
    Extracts court, section, insert number, legal name, registered seat,
    legal form, registration date, activities, executives, owners, contributions,
    acting on behalf, registered capital, and update timestamps.
    """
    soup = BeautifulSoup(html_content, "lxml")
    
    executives = []
    owners = []
    address = {}
    capital = ""
    capital_amount = ""
    capital_paid = ""
    capital_details = {}
    activities = []
    activities_detailed = []
    contributions = {}
    
    court = ""
    section = ""
    insert_number = ""
    legal_name = ""
    legal_name_since = ""
    registration_date = ""
    legal_form = ""
    legal_form_since = ""
    acting_on_behalf = ""
    data_updated_at = ""
    extract_created_at = ""
    
    # 1. Header extraction: Court name
    src_td = soup.find("td", class_="src")
    if src_td:
        c_m = re.search(r"Výpis z Obchodného registra\s+(.+)", src_td.get_text(strip=True))
        if c_m:
            court_raw = c_m.group(1).strip()
            # Convert grammatical cases into clean nominative form
            court = court_raw.replace("Okresného súdu", "Okresný súd").replace("Mestského súdu", "Mestský súd")
            
    # 2. Section & Insert number (Oddiel a Vložka číslo)
    for td in soup.find_all("td"):
        tl = td.find("span", class_="tl")
        ra = td.find("span", class_="ra")
        if tl and ra:
            t_text = tl.get_text(strip=True).lower()
            if "oddiel" in t_text and not section:
                section = ra.get_text(strip=True)
            elif ("vložka" in t_text or "vlozka" in t_text) and not insert_number:
                insert_number = ra.get_text(strip=True)

    # 3. Timestamps at the bottom of extract
    for tr in soup.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) == 2:
            t0 = tds[0].get_text(strip=True).lower()
            t1 = tds[1].get_text(strip=True)
            if "dátum aktualizácie" in t0 or "datum aktualizacie" in t0:
                data_updated_at = t1.strip().lstrip("&nbsp;").strip()
            elif "dátum výpisu" in t0 or "datum vypisu" in t0:
                extract_created_at = t1.strip().lstrip("&nbsp;").strip()

    # 4. Iterate through all outer tables
    for table in soup.find_all("table"):
        rows = table.find_all("tr", recursive=False)
        if not rows:
            continue
        
        first_row = rows[0]
        cells = first_row.find_all("td", recursive=False)
        if len(cells) < 2:
            continue
            
        left_td = cells[0]
        right_td = cells[1]
        
        span_tl = left_td.find("span", class_="tl")
        if not span_tl:
            continue
            
        label_raw = span_tl.get_text()
        label_norm = normalize_label(label_raw)
        
        nested_tables = right_td.find_all("table")
        active_entries = []
        for nt in nested_tables:
            if nt.find("strike"):
                continue  # Skip historical/deleted records
            active_entries.append(nt)
            
        if not active_entries and not nested_tables:
            if not right_td.find("strike"):
                active_entries = [right_td]

        # --- Obchodné meno ---
        if label_norm in ("obchodne meno", "obchodne meno subjektu"):
            if active_entries:
                td1 = active_entries[0].find("td") or active_entries[0]
                lines = get_br_split_lines(td1)
                if lines:
                    legal_name = lines[0]
                m_since = re.search(r'\(od:\s*(\d{2}\.\d{2}\.\d{4})\)', active_entries[0].get_text())
                if m_since:
                    legal_name_since = m_since.group(1)

        # --- Sídlo (Address) ---
        elif label_norm == "sidlo":
            if active_entries:
                td1 = active_entries[0].find("td") or active_entries[0]
                lines = get_br_split_lines(td1)
                
                addr_lines = []
                addr_since = ""
                for l in lines:
                    m_s = re.search(r'\(od:\s*(\d{2}\.\d{2}\.\d{4})\)', l)
                    if m_s:
                        addr_since = m_s.group(1)
                    if l.startswith("(od:") or l.startswith("(do:"):
                        continue
                    addr_lines.append(l)
                
                raw_addr_text = ", ".join(addr_lines)
                postal_match = re.search(r'\b\d{3}\s?\d{2}\b', raw_addr_text)
                postal_formatted = postal_match.group(0) if postal_match else ""
                postal_clean = postal_formatted.replace(" ", "") if postal_formatted else ""
                
                street = ""
                city = ""
                if len(addr_lines) >= 2:
                    street = addr_lines[0]
                    city_cand = " ".join(addr_lines[1:])
                    if postal_formatted:
                        city_cand = city_cand.replace(postal_formatted, "").strip()
                    city = re.sub(r'[\s,]+', ' ', city_cand).strip()
                elif len(addr_lines) == 1:
                    parts = [p.strip() for p in addr_lines[0].split(",") if p.strip()]
                    if len(parts) >= 2:
                        street = parts[0]
                        city_cand = ", ".join(parts[1:])
                        if postal_formatted:
                            city_cand = city_cand.replace(postal_formatted, "").strip()
                        city = re.sub(r'[\s,]+', ' ', city_cand).strip()
                    else:
                        street = addr_lines[0]
                
                formatted_addr = f"{street}, {postal_formatted} {city}".strip(", ") if (street and city) else raw_addr_text
                
                address = {
                    "street": street or raw_addr_text,
                    "city": city,
                    "postal_code": postal_clean,
                    "postal_code_formatted": postal_formatted,
                    "formatted_address": formatted_addr,
                    "since": addr_since
                }

        # --- Deň zápisu ---
        elif label_norm in ("den zapisu", "datum zapisu"):
            if active_entries:
                txt = active_entries[0].get_text()
                m_date = re.search(r'\b\d{2}\.\d{2}\.\d{4}\b', txt)
                if m_date:
                    registration_date = m_date.group(0)

        # --- Právna forma ---
        elif label_norm in ("pravna forma", "pravna forma subjektu"):
            if active_entries:
                td1 = active_entries[0].find("td") or active_entries[0]
                lines = get_br_split_lines(td1)
                if lines:
                    legal_form = lines[0]
                m_since = re.search(r'\(od:\s*(\d{2}\.\d{2}\.\d{4})\)', active_entries[0].get_text())
                if m_since:
                    legal_form_since = m_since.group(1)

        # --- Štatutárny orgán (Executives) ---
        elif label_norm in ("statutarny organ", "predstavenstvo"):
            active_role = "konateľ"
            for entry in active_entries:
                td1 = entry.find("td") or entry
                person_link = td1.find("a", href=lambda h: h and "hladaj_osoba.asp" in h)
                
                if person_link:
                    name = normalize_text(person_link.get_text())
                    lines = get_br_split_lines(td1, decompose_links=True)
                    raw_entry_text = entry.get_text()
                    
                    since = ""
                    birth_date = ""
                    
                    b_match = re.search(r'Dátum narodenia:\s*(\d{2}\.\d{2}\.\d{4})', raw_entry_text)
                    if b_match:
                        birth_date = b_match.group(1)
                        
                    s_match = re.search(r'Vznik funkcie:\s*(\d{2}\.\d{2}\.\d{4})', raw_entry_text)
                    if s_match:
                        since = s_match.group(1)
                    else:
                        od_match = re.search(r'\(od:\s*(\d{2}\.\d{2}\.\d{4})\)', raw_entry_text)
                        if od_match:
                            since = od_match.group(1)
                            
                    is_rfo = bool(
                        entry.find("img", src=re.compile(r'icon_(ifo|stot)_green'))
                        or "stotožnená" in raw_entry_text
                        or "stotoznena" in raw_entry_text
                    )

                    address_lines = []
                    for line in lines:
                        if not any(phrase in line.lower() for phrase in ("osoba je stotoznena", "osoba ma zapisane", "vznik funkcie", "vznik clenstva")):
                            if not (line.startswith("(od:") or line.startswith("(do:")):
                                address_lines.append(line)
                                
                    addr_str = ", ".join(address_lines) if address_lines else ""
                    if not addr_str and birth_date:
                        addr_str = f"Dátum narodenia: {birth_date}"
                        
                    executives.append({
                        "name": name,
                        "role": active_role,
                        "address": addr_str,
                        "birth_date": birth_date,
                        "since": since,
                        "is_rfo_identified": is_rfo,
                        "type": "PERSON"
                    })
                else:
                    role_text = normalize_text(td1.get_text())
                    role_text = re.sub(r'\s*\(od:\s*[\d\.]+\)\s*$', '', role_text).strip()
                    if role_text:
                        active_role = role_text

        # --- Spoločníci / Akcionár (Owners) ---
        elif label_norm in ("spolocnici", "akcionar"):
            for entry in active_entries:
                td1 = entry.find("td") or entry
                raw_entry_text = entry.get_text()
                
                since = ""
                od_match = re.search(r'\(od:\s*(\d{2}\.\d{2}\.\d{4})\)', raw_entry_text)
                if od_match:
                    since = od_match.group(1)
                    
                person_link = td1.find("a", href=lambda h: h and ("hladaj_osoba.asp" in h or "hladaj_subjekt.asp" in h))
                
                name = ""
                address_lines = []
                lines = get_br_split_lines(td1, decompose_links=True) if person_link else get_br_split_lines(td1)
                
                if person_link:
                    name = normalize_text(person_link.get_text())
                    for line in lines:
                        if not any(phrase in line.lower() for phrase in ("osoba je stotoznena", "osoba ma zapisane")):
                            if not (line.startswith("(od:") or line.startswith("(do:")):
                                address_lines.append(line)
                else:
                    if lines:
                        name = lines[0]
                        for l in lines[1:]:
                            if not any(phrase in l.lower() for phrase in ("osoba je stotoznena", "osoba ma zapisane")):
                                if not (l.startswith("(od:") or l.startswith("(do:")):
                                    address_lines.append(l)

                raw_full = " ".join(lines)
                is_company = False
                ico = None
                
                ico_match = re.search(r'IČO:\s*([\d\s]+)', raw_entry_text)
                if ico_match:
                    is_company = True
                    ico = re.sub(r'\s+', '', ico_match.group(1))
                    
                if any(term in name.lower() for term in ("s.r.o.", "s. r. o.", "a.s.", "a. s.", "spol. s r.o.", "k.s.", "v.o.s.")):
                    is_company = True
                    
                clean_name = re.sub(r'IČO:\s*[\d\s]+', '', name).strip()
                
                birth_date = None
                b_match = re.search(r'Dátum narodenia:\s*(\d{2}\.\d{2}\.\d{4})', raw_entry_text)
                if b_match:
                    birth_date = b_match.group(1)
                    
                is_rfo = bool(
                    entry.find("img", src=re.compile(r'icon_(ifo|stot)_green'))
                    or "stotožnená" in raw_entry_text
                    or "stotoznena" in raw_entry_text
                )

                # Filter IČO out of address lines
                cleaned_addr_lines = []
                for l in address_lines:
                    l_c = re.sub(r'IČO:\s*[\d\s]+', '', l).strip()
                    if l_c:
                        cleaned_addr_lines.append(l_c)
                        
                addr_str = ", ".join(cleaned_addr_lines) if cleaned_addr_lines else ""
                if not addr_str and birth_date:
                    addr_str = f"Dátum narodenia: {birth_date}"

                if clean_name:
                    owners.append({
                        "name": clean_name,
                        "type": "COMPANY" if is_company else "PERSON",
                        "ico": ico,
                        "birth_date": birth_date,
                        "address": addr_str,
                        "share": None,
                        "deposit": None,
                        "paid": None,
                        "since": since,
                        "is_rfo_identified": is_rfo
                    })

        # --- Výška vkladu každého spoločníka (Contributions) ---
        elif label_norm == "vyska vkladu kazdeho spolocnika":
            for entry in active_entries:
                td1 = entry.find("td") or entry
                lines = get_br_split_lines(td1)
                if len(lines) >= 2:
                    c_name = lines[0]
                    clean_c_name = re.sub(r'IČO:\s*[\d\s]+', '', c_name).strip()
                    
                    full_contrib_txt = " ".join(lines[1:])
                    vklad_m = re.search(r'Vklad:\s*([\d\s]+)\s*([A-Z]{3})?', full_contrib_txt)
                    splatene_m = re.search(r'Splatené:\s*([\d\s]+)\s*([A-Z]{3})?', full_contrib_txt)
                    
                    dep_curr = vklad_m.group(2) or "EUR" if vklad_m else "EUR"
                    deposit = f"{vklad_m.group(1).strip()} {dep_curr}".strip() if vklad_m else ""
                    paid = f"{splatene_m.group(1).strip()} {dep_curr}".strip() if splatene_m else ""
                    
                    contrib_lines = []
                    for l in lines[1:]:
                        if l.startswith("(od:") or l.startswith("(do:"):
                            continue
                        contrib_lines.append(l)
                    raw_share = " ".join(contrib_lines)
                    
                    contributions[normalize_label(clean_c_name)] = {
                        "deposit": deposit,
                        "paid": paid,
                        "share": raw_share
                    }

        # --- Konanie menom spoločnosti ---
        elif label_norm in ("konanie menom spolocnosti", "sposob konania"):
            if active_entries:
                td1 = active_entries[0].find("td") or active_entries[0]
                lines = get_br_split_lines(td1)
                acting_lines = [l for l in lines if not (l.startswith("(od:") or l.startswith("(do:"))]
                acting_on_behalf = " ".join(acting_lines)

        # --- Výška základného imania (Capital) ---
        elif label_norm == "vyska zakladneho imania":
            if active_entries:
                td1 = active_entries[0].find("td") or active_entries[0]
                cap_text = normalize_text(td1.get_text(separator=" "))
                cap_text = re.sub(r'\s*\(od:\s*[\d\.]+\)\s*$', '', cap_text).strip()
                capital = cap_text
                
                vklad_m = re.search(r'([\d\s]+)\s*(EUR|SKK)', cap_text)
                splat_m = re.search(r'Rozsah splatenia:\s*([\d\s]+)\s*(EUR|SKK)', cap_text)
                curr = (vklad_m.group(2) if vklad_m else "EUR")
                capital_amount = f"{vklad_m.group(1).strip()} {curr}".strip() if vklad_m else cap_text
                capital_paid = f"{splat_m.group(1).strip()} {curr}".strip() if splat_m else capital_amount
                capital_details = {
                    "amount": capital_amount,
                    "paid": capital_paid,
                    "currency": curr
                }

        # --- Predmety podnikania (Activities) ---
        elif label_norm == "predmet podnikania cinnosti":
            for entry in active_entries:
                tds = entry.find_all("td")
                td1 = tds[0] if tds else entry
                act_text = normalize_text(td1.get_text())
                act_clean = re.sub(r'\s*\(od:\s*[\d\.]+\)\s*$', '', act_text).strip()
                since = ""
                raw_entry_txt = entry.get_text()
                m_since = re.search(r'\(od:\s*(\d{2}\.\d{2}\.\d{4})\)', raw_entry_txt)
                if m_since:
                    since = m_since.group(1)
                if act_clean:
                    activities.append(act_clean)
                    activities_detailed.append({
                        "name": act_clean,
                        "since": since
                    })

    # Merge contributions into owners
    for owner in owners:
        owner_key = normalize_label(owner["name"])
        if owner_key in contributions:
            c = contributions[owner_key]
            owner["share"] = c["share"]
            owner["deposit"] = c["deposit"]
            owner["paid"] = c["paid"]
        else:
            # Try fuzzy matching in case of minor variations
            for contrib_key, c in contributions.items():
                if owner_key in contrib_key or contrib_key in owner_key:
                    owner["share"] = c["share"]
                    owner["deposit"] = c["deposit"]
                    owner["paid"] = c["paid"]
                    break

    return {
        "court": court,
        "section": section,
        "insert_number": insert_number,
        "legal_name": legal_name,
        "legal_name_since": legal_name_since,
        "registration_date": registration_date,
        "legal_form": legal_form,
        "legal_form_since": legal_form_since,
        "acting_on_behalf": acting_on_behalf,
        "address": address,
        "executives": executives,
        "owners": owners,
        "capital": capital,
        "capital_amount": capital_amount,
        "capital_paid": capital_paid,
        "capital_details": capital_details,
        "activities": activities,
        "activities_detailed": activities_detailed,
        "data_updated_at": data_updated_at,
        "extract_created_at": extract_created_at
    }
