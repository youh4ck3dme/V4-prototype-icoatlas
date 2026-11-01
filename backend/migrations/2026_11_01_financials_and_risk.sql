-- Financials, Risk and IBAN columns for atlas_companies
-- run_production_migrations.sh re-applies every file on each run, so everything here is idempotent.
--
-- financials (JSONB): latest statement + yearly history, e.g.
--   {
--     "year": 2024, "template": "687", "period_from": "2024-01", "period_to": "2024-12",
--     "assets": 1250000.0, "liabilities": 890000.0, "equity": 360000.0,
--     "revenue": 2450000.0, "profit": 185000.0,
--     "source": "RUZ", "raw": {},
--     "history": [ { "year": 2023, ... same keys without "history" ... } ]
--   }
-- risk_score: 0..10, same scale as the existing risk scoring (higher = riskier). NULL = not scored yet.
-- risk_flags (JSONB): list of flags, e.g. [{"code": "LIQUIDATION", "weight": 8, "source": "ORSR"}]
-- iban_verified: NULL = not checked, true/false = result of the last check.
-- Raw IBAN check responses go to company_sources (source_system = 'FS_IBAN').

ALTER TABLE atlas_companies ADD COLUMN IF NOT EXISTS financials JSONB;
ALTER TABLE atlas_companies ADD COLUMN IF NOT EXISTS last_financial_year INT;
ALTER TABLE atlas_companies ADD COLUMN IF NOT EXISTS risk_score INT;
ALTER TABLE atlas_companies ADD COLUMN IF NOT EXISTS risk_flags JSONB;
ALTER TABLE atlas_companies ADD COLUMN IF NOT EXISTS iban_verified BOOLEAN;
ALTER TABLE atlas_companies ADD COLUMN IF NOT EXISTS iban_verified_at TIMESTAMPTZ;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'chk_atlas_companies_risk_score'
      AND conrelid = 'atlas_companies'::regclass
  ) THEN
    ALTER TABLE atlas_companies
      ADD CONSTRAINT chk_atlas_companies_risk_score
      CHECK (risk_score IS NULL OR risk_score BETWEEN 0 AND 10);
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_atlas_companies_last_financial_year ON atlas_companies(last_financial_year);
CREATE INDEX IF NOT EXISTS idx_atlas_companies_risk_score ON atlas_companies(risk_score);
