# Country JSON Templates

This directory contains standardized JSON schema templates for company data from different countries.

## Available Templates

### 🇸🇰 Slovakia (`sk_template.json`)

- **Primary ID**: IČO (8-digit number)
- **Data Sources**: ORSR, RUZ, ZRSR, RPO
- **Key Fields**: ico, dic, ic_dph, registration_id, executives, shareholders, beneficial_owners

### 🇨🇿 Czech Republic (`cz_template.json`)

- **Primary ID**: IČO (8-digit number)
- **Data Sources**: ARES, Commercial Register
- **Key Fields**: ico, dic, ic_dph, registration_court, nace_code

### 🇵🇱 Poland (`pl_template.json`)

- **Primary ID**: NIP (10-digit number)
- **Data Sources**: KRS, CEIDG, GUS, VAT White List
- **Key Fields**: nip, krs, regon, pkd_code, white_list_vat, bank_accounts

### 🇭🇺 Hungary (`hu_template.json`)

- **Primary ID**: Adószám (Tax number)
- **Data Sources**: NAV, Company Register
- **Key Fields**: adoszam, cegjegyzekszam, teaor_code, vat_number

## Usage

### Validation

These templates follow JSON Schema Draft 7 specification and can be used to validate API responses:

```python
import json
import jsonschema

# Load schema
with open('templates/sk_template.json') as f:
    schema = json.load(f)

# Validate data
jsonschema.validate(instance=company_data, schema=schema)
```

### Field Mapping

All templates include standardized fields:

- **country**: ISO 3166-1 alpha-2 country code
- **name**: Official company name
- **legal_form**: Legal structure
- **address**, **street**, **city**, **zip**: Address components
- **executives**: List of statutory representatives
- **shareholders**: List of owners/partners
- **founded**: Registration date (YYYY-MM-DD format)
- **status**: Current company status
- **financial_data**: Financial indicators (optional)
- **risk_score**: Calculated risk score 0-100 (optional)

### Country-Specific Fields

#### Slovakia

- `dic`: Tax ID (10 digits)
- `ic_dph`: VAT number (SK + 10 digits)
- `registration_id`: Vložka number
- `beneficial_owners`: From RPO register

#### Czech Republic

- `dic`: Tax ID (CZ + 8-10 digits)
- `registration_court`: Rejstříkový soud
- `nace_code`: Economic activity code

#### Poland

- `nip`: Tax ID (10 digits)
- `krs`: Court register number
- `regon`: Statistical number
- `white_list_vat`: VAT white list status
- `bank_accounts`: Registered bank accounts

#### Hungary

- `adoszam`: Tax number (format: 12345678-1-23)
- `cegjegyzekszam`: Company registration number
- `teaor_code`: Economic activity code
- `statistical_number`: Statistical identifier

## Examples

See the `examples/` directory for sample JSON instances for each country.

## Notes

- All dates use ISO 8601 format (YYYY-MM-DD)
- Postal codes follow country-specific formats
- Financial data is optional and may not be available for all companies
- Risk scores are calculated values and may vary based on available data
