import hashlib
from datetime import datetime
import uuid
import httpx
from typing import Dict
from .models import V4APIError

class HUNAVClient:
    """Klient pre maďarský NAV Online Számla"""
    
    BASE_URL = "https://api.onlineszamla.nav.gov.hu/invoiceService/v3"
    
    def __init__(self, login: str, password: str, signing_key: str, tax_number: str):
        self.login = login
        self.password_hash = hashlib.sha512(password.encode()).hexdigest().upper()
        self.signing_key = signing_key
        self.tax_number = tax_number
    
    def _compute_signature(self, request_id: str, timestamp: str) -> str:
        """Výpočet SHA-512 podpisu"""
        ts_clean = timestamp.replace("-", "").replace(":", "").replace(".", "").replace("T", "").replace("Z", "")
        data = f"{request_id}{ts_clean}{self.signing_key}"
        return hashlib.sha512(data.encode()).hexdigest().upper()
    
    def _parse_xml_response(self, text: str) -> Dict:
        # Simplistic XML parsing or return raw text for now
        # Ideally use xml.etree.ElementTree or BeautifulSoup
        return {"raw_xml": text} 

    async def query_taxpayer(self, tax_number: str) -> Dict:
        """Overenie existencie daňovníka"""
        request_id = f"RID{uuid.uuid4().hex[:20].upper()}"
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
        signature = self._compute_signature(request_id, timestamp)
        
        xml_request = f"""<?xml version="1.0" encoding="UTF-8"?>
        <QueryTaxpayerRequest xmlns="http://schemas.nav.gov.hu/OSA/3.0/api">
            <header>
                <requestId>{request_id}</requestId>
                <timestamp>{timestamp}</timestamp>
                <requestVersion>3.0</requestVersion>
                <headerVersion>1.0</headerVersion>
            </header>
            <user>
                <login>{self.login}</login>
                <passwordHash>{self.password_hash}</passwordHash>
                <taxNumber>{self.tax_number}</taxNumber>
                <requestSignature>{signature}</requestSignature>
            </user>
            <software>
                <softwareId>ILUMINATI-V4</softwareId>
                <softwareName>ILUMINATI SYSTEM</softwareName>
                <softwareOperation>LOCAL_SOFTWARE</softwareOperation>
                <softwareMainVersion>5.0</softwareMainVersion>
                <softwareDevName>ILUMINATI Team</softwareDevName>
                <softwareDevContact>support@iluminati.sk</softwareDevContact>
            </software>
            <taxNumber>{tax_number}</taxNumber>
        </QueryTaxpayerRequest>"""
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.BASE_URL}/queryTaxpayer",
                    content=xml_request,
                    headers={"Content-Type": "application/xml"}
                )
                return self._parse_xml_response(response.text)
            except Exception as e:
                raise V4APIError(f"NAV Request failed: {e}")