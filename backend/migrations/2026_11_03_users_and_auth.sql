-- Users, API keys, search history and favorites for the v5 backend
-- (ported from backend_legacy_20251229_195800 SQLAlchemy models).
-- run_production_migrations.sh re-applies every file on each run, so everything here is idempotent.

CREATE TABLE IF NOT EXISTS users (
  id BIGSERIAL PRIMARY KEY,
  email TEXT NOT NULL,
  password_hash TEXT NOT NULL,
  full_name TEXT,
  tier TEXT NOT NULL DEFAULT 'free',
  is_active BOOLEAN NOT NULL DEFAULT true,
  is_verified BOOLEAN NOT NULL DEFAULT false,
  consent_given BOOLEAN NOT NULL DEFAULT false,
  consent_at TIMESTAMPTZ,
  consent_ip TEXT,
  consent_user_agent TEXT,
  document_versions JSONB,
  stripe_customer_id TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_login_at TIMESTAMPTZ
);

-- e-mail je unikátny bez ohľadu na veľkosť písmen
CREATE UNIQUE INDEX IF NOT EXISTS uq_users_email_lower ON users (lower(email));
CREATE UNIQUE INDEX IF NOT EXISTS uq_users_stripe_customer ON users (stripe_customer_id) WHERE stripe_customer_id IS NOT NULL;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_users_tier' AND conrelid = 'users'::regclass) THEN
    ALTER TABLE users ADD CONSTRAINT chk_users_tier CHECK (tier IN ('free', 'pro', 'enterprise'));
  END IF;
END $$;

-- API kľúče: uložený je len SHA-256 hash, celý kľúč sa ukáže iba raz pri vytvorení
CREATE TABLE IF NOT EXISTS api_keys (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  prefix TEXT NOT NULL,
  key_hash TEXT NOT NULL,
  permissions TEXT[] NOT NULL DEFAULT ARRAY['read'],
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at TIMESTAMPTZ,
  last_used_at TIMESTAMPTZ,
  revoked_at TIMESTAMPTZ,
  CONSTRAINT uq_api_keys_hash UNIQUE (key_hash)
);
CREATE INDEX IF NOT EXISTS idx_api_keys_user ON api_keys(user_id);

-- História vyhľadávaní je vždy viazaná na používateľa (legacy ju vracal všetkým)
CREATE TABLE IF NOT EXISTS search_history (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  query TEXT NOT NULL,
  country TEXT,
  atlas_id TEXT,
  result_count INT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_search_history_user_time ON search_history(user_id, created_at DESC);

CREATE TABLE IF NOT EXISTS favorite_companies (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  company_identifier TEXT NOT NULL,
  company_name TEXT NOT NULL,
  country TEXT NOT NULL,
  company_data JSONB,
  risk_score DOUBLE PRECISION,
  risk_factors JSONB,
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_favorite_per_user UNIQUE (user_id, company_identifier, country)
);
CREATE INDEX IF NOT EXISTS idx_favorite_companies_user ON favorite_companies(user_id, created_at DESC);
