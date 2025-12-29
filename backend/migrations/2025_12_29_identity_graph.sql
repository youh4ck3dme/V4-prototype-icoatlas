-- Identity Graph Migration for V4 Atlas
-- Enable UUID generator
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Canonical company entity (1 row = 1 firma)
CREATE TABLE IF NOT EXISTS atlas_companies (
  atlas_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  country TEXT NOT NULL,

  legal_name TEXT,
  status TEXT,
  legal_form TEXT,

  registration_number TEXT,     -- napr. SK ORSR "208/B" alebo HU/CZ/PL ak vieš
  street TEXT,
  city TEXT,
  postal_code TEXT,
  region TEXT,

  capital_amount NUMERIC,
  capital_currency TEXT,
  employees_range TEXT,

  nace_codes TEXT[],            -- voliteľne (keď budeš mať)
  source_api TEXT,              -- posledný zdroj
  fetched_at TIMESTAMPTZ,       -- posledný fetch z externého zdroja

  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_atlas_companies_country ON atlas_companies(country);
CREATE INDEX IF NOT EXISTS idx_atlas_companies_legal_name ON atlas_companies(legal_name);

-- Identifier map (kľúčová tabuľka)
CREATE TABLE IF NOT EXISTS company_identifiers (
  id BIGSERIAL PRIMARY KEY,
  atlas_id UUID NOT NULL REFERENCES atlas_companies(atlas_id) ON DELETE CASCADE,

  country TEXT NOT NULL,
  id_type TEXT NOT NULL,          -- ICO, VAT, DIC, NIP, KRS, REGON, ADOSZAM, CEGJEGYZEKSZAM...
  value TEXT NOT NULL,            -- canonical string (napr SK2020..., 14906428-2-06, 01-09-562739)
  value_digits TEXT NOT NULL,     -- digits-only pre extrémne rýchly lookup

  is_primary BOOLEAN NOT NULL DEFAULT false,
  is_verified BOOLEAN NOT NULL DEFAULT false,

  source TEXT,                    -- ORSR/ZRSR/ARES/KRS/NAV/...
  first_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT uq_identifier UNIQUE (country, id_type, value_digits)
);

CREATE INDEX IF NOT EXISTS idx_company_identifiers_digits ON company_identifiers(value_digits);
CREATE INDEX IF NOT EXISTS idx_company_identifiers_atlas_id ON company_identifiers(atlas_id);

-- Raw source snapshots (debug + audit + reprodukovateľnosť)
CREATE TABLE IF NOT EXISTS company_sources (
  id BIGSERIAL PRIMARY KEY,
  atlas_id UUID NOT NULL REFERENCES atlas_companies(atlas_id) ON DELETE CASCADE,

  source_system TEXT NOT NULL,      -- ORSR, ZRSR, ARES, KRS, NAV...
  source_ref TEXT,                  -- endpoint / url / route
  request_id TEXT,                  -- čo user zadal (raw)
  http_status INT,
  fetched_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  payload JSONB                      -- raw JSON (alebo normalize->json)
);

CREATE INDEX IF NOT EXISTS idx_company_sources_atlas_id ON company_sources(atlas_id);
CREATE INDEX IF NOT EXISTS idx_company_sources_source_system ON company_sources(source_system);

-- Merge audit (keď zistíš, že 2 atlas_id sú tá istá firma)
CREATE TABLE IF NOT EXISTS company_merges (
  id BIGSERIAL PRIMARY KEY,
  survivor_atlas_id UUID NOT NULL REFERENCES atlas_companies(atlas_id) ON DELETE CASCADE,
  merged_atlas_id UUID NOT NULL REFERENCES atlas_companies(atlas_id) ON DELETE CASCADE,
  reason TEXT,
  merged_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
