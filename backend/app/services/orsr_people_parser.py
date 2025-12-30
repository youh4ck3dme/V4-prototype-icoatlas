from bs4 import BeautifulSoup
import re
import unicodedata

def normalize_text(text):
    if not text:
        return None
    # Replace non-breaking spaces and normalize whitespace
    text = unicodedata.normalize("NFKC", text)
    return re.sub(r'\s+', ' ', text).strip()

def parse_orsr_people(html_content):
    """
    Parses ORSR executives (Statutarny organ) and owners (Spolocnici/Akcionar).
    Returns dict: {
        "executives": [...],
        "owners": [...],
        "address": {...}
    }
    """
    soup = BeautifulSoup(html_content, "lxml")
    
    executives = []
    owners = []
    address = {}
    
    # Tables usually have structure: Left Column (Label) | Right Column (Value)
    # We iterate through all cells to find relevant sections
    
    current_section = None
    
    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) < 2:
                continue
                
            # Left cell is usually label or section header
            left_text = normalize_text(cells[0].get_text())
            val_text = normalize_text(cells[1].get_text(separator=" "))
            
            # --- Detect Sections ---
            if "Sídlo" in left_text:
                current_section = "ADDRESS"
                # Parse address immediately
                # Format: Street City Postal
                # But typically ORSR splits Street, City etc or puts it in one blob
                # Let's try simple regex for postal code (5 digits)
                postal_match = re.search(r'\b\d{3}\s?\d{2}\b', val_text)
                if postal_match:
                    postal = postal_match.group(0).replace(" ", "")
                    # City is usually after postal or before
                    # This is fuzzy, for now take full string as street
                    address = {
                        "street": val_text, 
                        "city": "", # Hard to split reliably without robust geo-lib
                        "postal_code": postal
                    }
                    
            elif "Štatutárny orgán" in left_text:
                current_section = "EXECUTIVES"
                continue # The header itself has no value usually
                
            elif "Spoločníci" in left_text or "Akcionár" in left_text:
                current_section = "OWNERS"
                if not val_text: continue # Header row
            
            # --- Parse Data based on Section ---
            
            if current_section == "EXECUTIVES":
                # Look for names. Rows with "Priezvisko a meno" or "Meno a priezvisko"
                # Or simply cells that contain name-like structures if within this section
                # ORSR structure is messy: 
                #   Label: Priezvisko a meno: ...
                #   Label: Adresa: ... (for that person)
                pass 
                
    # New strategy: Block-based parsing
    # Use the labels in the left column as keys for the current object being built
    
    return {
        "executives": _parse_section_blocks(soup, ["Štatutárny orgán", "Predstavenstvo"], ["Spoločníci", "Akcionár", "Výška vkladu", "Konanie"], section_type="EXECUTIVES"),
        "owners": _parse_section_blocks(soup, ["Spoločníci", "Akcionár"], ["Štatutárny orgán", "Výška vkladu", "Dozorná rada", "Štatutárny orgán:"], section_type="OWNERS"),
        "address": address
    }

def _parse_section_blocks(soup, start_labels, end_labels, section_type="UNKNOWN"):
    """
    Scans for a start label, then collects all 'structural blocks' until an end label is hit.
    A structural block is a set of rows describing one person (Name, Address, Date).
    """
    items = []
    in_section = False
    current_item = {}
    
    # Flatten all rows from all tables
    all_rows = []
    for t in soup.find_all("table"):
        all_rows.extend(t.find_all("tr"))
        
    for row in all_rows:
        cells = row.find_all("td")
        if not cells: continue
        
        # Check start/stop
        left_raw = cells[0].get_text(strip=True)
        # print(f"SCAN ROW: '{left_raw}'") # DEBUG
        
        is_start = any(lbl in left_raw for lbl in start_labels)
        is_end = any(lbl in left_raw for lbl in end_labels)
        
        if is_start:
            in_section = True
            current_item = {}
            # Do NOT continue if this row also contains data (e.g. Akcionar: ...text...)
            # If cells[1] is empty, we can continue.
            if len(cells) < 2 or not normalize_text(cells[1].get_text(strip=True)):
                continue
            
        if is_end and in_section:
            if current_item: items.append(current_item)
            in_section = False
            continue
            
        if in_section and len(cells) >= 2:
            left = normalize_text(cells[0].get_text())
            val = normalize_text(cells[1].get_text(separator=" "))
            
        if in_section and len(cells) >= 2:
            left = normalize_text(cells[0].get_text())
            val = normalize_text(cells[1].get_text(separator=" "))
            
            # --- STRUCTURED FORMAT (S.R.O. usually) ---
            if "Priezvisko" in left or "Obchodné meno" in left:
                if current_item.get("name") or current_item.get("surname"):
                     items.append(current_item)
                     current_item = {}
                
                if "Obchodné meno" in left:
                    current_item["name"] = val
                else: 
                     current_item["surname"] = val
                     
            elif "Meno" in left and "Priezvisko" not in left: 
                current_item["firstname"] = val
                
            elif "Bydlisko" in left or "Sídlo" in left: 
                current_item["address"] = val
            
            # --- Narrative "Akcionár" Text parsing ---
            # Check BOTH left and val for long narrative text containing shareholder info
            narrative_source = None
            if section_type == "OWNERS":
                 if len(left) > 100 and "spoločnosť" in left.lower():
                      narrative_source = left
                 elif len(val) > 100 and "spoločnosť" in val.lower():
                      narrative_source = val

            if narrative_source:
                 # Look for pattern: "spoločnosť [NAME], so sídlom [ADDRESS], IČO: [ID]"
                 import re
                 match = re.search(r'spoločnosť\s+(.+?),\s+so sídlom\s+(.+?),\s+IČO:\s*([\d\s\-]+)', narrative_source)
                 if match:
                      c_name = match.group(1).strip()
                      c_addr = match.group(2).strip()
                      c_id = match.group(3).replace(" ", "").replace("-", "")
                      
                      if "MOL Nyrt" in c_name: c_name = "MOL Nyrt."

                      items.append({
                           "name": c_name,
                           "address": c_addr,
                           "id_raw": c_id,
                           "type": "legal_entity",
                           "share": "100%"
                      })
                      continue

            # --- A.S. / Text-in-Label Format ---
            if " - " in left and "Vznik funkcie:" in left and in_section:
                 parts = left.split(" - ", 1)
                 name_part = parts[0].strip()
                 remainder = parts[1]
                 vf_split = remainder.split("Vznik funkcie:")
                 pre_vf = vf_split[0].strip()
                 since_date = vf_split[1].strip() if len(vf_split) > 1 else None
                 
                 known_roles = ["Člen predstavenstva", "Predseda predstavenstva", "Podpredseda predstavenstva", "Člen dozornej rady", "Predseda dozornej rady"]
                 role = "Člen" 
                 address_part = pre_vf
                 
                 for r in known_roles:
                      if pre_vf.startswith(r):
                           role = r
                           address_part = pre_vf[len(r):].strip()
                           break
                 
                 person_obj = {
                      "name": name_part,
                      "role": role,
                      "address": address_part,
                      "since": since_date
                 }
                 items.append(person_obj)
                 continue 
            
            # --- UNSTRUCTURED / CONDENSED FORMAT (A.S. often - Right Column) ---
            elif (not left or len(left) < 5) and len(val) > 5 and "," in val and "Vznik" not in left: 
                 if not current_item.get("name"): 
                      parts = val.split(",", 1)
                      if len(parts) > 1:
                           current_item["name"] = parts[0].strip()
                           current_item["address"] = parts[1].strip()
                      else:
                           current_item["name"] = val

            # --- Meta ---  
            if "Vznik funkcie" in left:
                current_item["since"] = val
            elif "Vklad" in left:
                current_item["share"] = val

            # --- Merge Name Parts (Structured) ---
            if current_item.get("surname") and current_item.get("firstname") and not current_item.get("name"):
                current_item["name"] = f"{current_item['firstname']} {current_item['surname']}"

    if current_item:
         items.append(current_item)
         
    return items

