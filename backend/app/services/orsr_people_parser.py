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
    # strip accents, convert to lowercase, keep only alphanumeric and spaces
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

def parse_orsr_people(html_content):
    """
    Parses ORSR executives (Statutarny organ), owners (Spolocnici/Akcionar), 
    capital (Zakladne imanie), and activities (Predmety podnikania).
    Returns dict: {
        "executives": [...],
        "owners": [...],
        "address": {...},
        "capital": "...",
        "activities": [...]
    }
    """
    soup = BeautifulSoup(html_content, "lxml")
    
    executives = []
    owners = []
    address = {}
    capital = ""
    activities = []
    contributions = {}
    
    # Iterate through all outer tables
    for table in soup.find_all("table"):
        # We look for a structure where the first row has a left cell with class "tl" or a span with class "tl"
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
        
        # Find active nested tables in the right cell (ignore crossed-out ones)
        nested_tables = right_td.find_all("table")
        active_entries = []
        for nt in nested_tables:
            if nt.find("strike"):
                continue  # Skip deleted/historical records
            active_entries.append(nt)
            
        if not active_entries and not nested_tables:
            # Fallback if there are no nested tables but there is direct text
            if not right_td.find("strike"):
                active_entries = [right_td]

        # --- Parse Address ---
        if label_norm == "sidlo":
            if active_entries:
                td1 = active_entries[0].find("td") or active_entries[0]
                lines = get_br_split_lines(td1)
                
                # Exclude date lines like (od: 16.06.2022)
                addr_lines = []
                for l in lines:
                    if l.startswith("(od:") or l.startswith("(do:"):
                        continue
                    addr_lines.append(l)
                
                addr_text = ", ".join(addr_lines)
                
                # Try simple regex for postal code (5 digits)
                postal_match = re.search(r'\b\d{3}\s?\d{2}\b', addr_text)
                postal = postal_match.group(0).replace(" ", "") if postal_match else ""
                
                address = {
                    "street": addr_text,
                    "city": "",
                    "postal_code": postal
                }
                
        # --- Parse Executives (Štatutárny orgán / Predstavenstvo) ---
        elif label_norm in ("statutarny organ", "predstavenstvo"):
            active_role = "konateľ"
            for entry in active_entries:
                td1 = entry.find("td") or entry
                
                # Check for person/entity link
                person_link = td1.find("a", href=lambda h: h and "hladaj_osoba.asp" in h)
                
                if person_link:
                    name = normalize_text(person_link.get_text())
                    lines = get_br_split_lines(td1, decompose_links=True)
                    
                    since = ""
                    address_lines = []
                    for line in lines:
                        if "vznik funkcie" in line.lower() or "vznik clenstva" in line.lower():
                            date_match = re.search(r'\b\d{2}\.\d{2}\.\d{4}\b', line)
                            if date_match:
                                since = date_match.group(0)
                        else:
                            # Skip common system phrases and dates
                            if not any(phrase in line.lower() for phrase in ("osoba je stotoznena", "osoba ma zapisane", "vznik funkcie", "vznik clenstva")):
                                if not (line.startswith("(od:") or line.startswith("(do:")):
                                    address_lines.append(line)
                                
                    addr_str = ", ".join(address_lines) if address_lines else ""
                    
                    executives.append({
                        "name": name,
                        "role": active_role,
                        "address": addr_str,
                        "since": since
                    })
                else:
                    # It's a role designation, e.g. "konateľ" or "člen predstavenstva"
                    role_text = normalize_text(td1.get_text())
                    # Clean up date suffix if present
                    role_text = re.sub(r'\s*\(od:\s*[\d\.]+\)\s*$', '', role_text).strip()
                    if role_text:
                        active_role = role_text

        # --- Parse Owners / Partners (Spoločníci / Akcionár) ---
        elif label_norm in ("spolocnici", "akcionar"):
            for entry in active_entries:
                td1 = entry.find("td") or entry
                
                # Check for person link or company link
                person_link = td1.find("a", href=lambda h: h and ("hladaj_osoba.asp" in h or "hladaj_subjekt.asp" in h))
                
                name = ""
                address_lines = []
                
                if person_link:
                    name = normalize_text(person_link.get_text())
                    lines = get_br_split_lines(td1, decompose_links=True)
                    for line in lines:
                        if not any(phrase in line.lower() for phrase in ("osoba je stotoznena", "osoba ma zapisane")):
                            if not (line.startswith("(od:") or line.startswith("(do:")):
                                address_lines.append(line)
                else:
                    # Fallback for plain text name and address
                    lines = get_br_split_lines(td1)
                    if lines:
                        name = lines[0]
                        address_lines = []
                        for l in lines[1:]:
                            if not (l.startswith("(od:") or l.startswith("(do:")):
                                address_lines.append(l)
                        
                addr_str = ", ".join(address_lines) if address_lines else ""
                if name:
                    owners.append({
                        "name": name,
                        "address": addr_str,
                        "share": None
                    })
                    
        # --- Parse Contributions (Výška vkladu každého spoločníka) ---
        elif label_norm == "vyska vkladu kazdeho spolocnika":
            for entry in active_entries:
                td1 = entry.find("td") or entry
                lines = get_br_split_lines(td1)
                if len(lines) >= 2:
                    name = lines[0]
                    # Exclude date lines
                    contrib_lines = []
                    for l in lines[1:]:
                        if l.startswith("(od:") or l.startswith("(do:"):
                            continue
                        contrib_lines.append(l)
                    share_details = ", ".join(contrib_lines)
                    contributions[name] = share_details
                    
        # --- Parse Capital (Výška základného imania) ---
        elif label_norm == "vyska zakladneho imania":
            if active_entries:
                td1 = active_entries[0].find("td") or active_entries[0]
                cap_text = normalize_text(td1.get_text(separator=" "))
                cap_text = re.sub(r'\s*\(od:\s*[\d\.]+\)\s*$', '', cap_text).strip()
                capital = cap_text
                
        # --- Parse Activities (Predmety podnikania) ---
        elif label_norm == "predmet podnikania cinnosti":
            for entry in active_entries:
                td1 = entry.find("td") or entry
                act_text = normalize_text(td1.get_text())
                act_text = re.sub(r'\s*\(od:\s*[\d\.]+\)\s*$', '', act_text).strip()
                if act_text:
                    activities.append(act_text)

    # Merge contributions into owners
    for owner in owners:
        owner_name = owner["name"]
        for contrib_name, share in contributions.items():
            if normalize_label(owner_name) == normalize_label(contrib_name):
                owner["share"] = share
                break

    return {
        "executives": executives,
        "owners": owners,
        "address": address,
        "capital": capital,
        "activities": activities
    }
