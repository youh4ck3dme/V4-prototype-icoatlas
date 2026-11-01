"""
Applies backend/migrations/*.sql the same way run_production_migrations.sh does
(every file, in order, on every run) against a throwaway Postgres.

Runs only when TEST_DATABASE_URL points to an empty, disposable database, e.g.
  TEST_DATABASE_URL=postgresql://postgres@localhost:5432/atlas_test pytest backend/tests/test_migrations_sql.py
"""
import os
from pathlib import Path

import pytest

psycopg2 = pytest.importorskip("psycopg2")

DSN = os.getenv("TEST_DATABASE_URL")
MIGRATIONS = sorted((Path(__file__).resolve().parents[1] / "migrations").glob("*.sql"))

pytestmark = pytest.mark.skipif(not DSN, reason="TEST_DATABASE_URL not set")


@pytest.fixture()
def conn():
    c = psycopg2.connect(DSN)
    c.autocommit = True
    with c.cursor() as cur:
        cur.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
    yield c
    c.close()


def apply_all(conn):
    with conn.cursor() as cur:
        for path in MIGRATIONS:
            cur.execute(path.read_text(encoding="utf-8"))


def test_migrations_are_idempotent(conn):
    apply_all(conn)
    apply_all(conn)  # production runner re-applies every file


def test_financials_risk_iban_columns(conn):
    apply_all(conn)
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT column_name, data_type FROM information_schema.columns
            WHERE table_name = 'atlas_companies'
            """
        )
        cols = dict(cur.fetchall())
    assert cols["financials"] == "jsonb"
    assert cols["last_financial_year"] == "integer"
    assert cols["risk_score"] == "integer"
    assert cols["risk_flags"] == "jsonb"
    assert cols["iban_verified"] == "boolean"
    assert cols["iban_verified_at"] == "timestamp with time zone"


def test_existing_rows_survive_and_risk_score_is_bounded(conn):
    # Apply only the files that existed before this migration, add data, then apply all.
    with conn.cursor() as cur:
        for path in MIGRATIONS:
            if path.name < "2026_11_01":
                cur.execute(path.read_text(encoding="utf-8"))
        cur.execute("INSERT INTO atlas_companies (country, legal_name) VALUES ('SK', 'Existing s.r.o.')")
    apply_all(conn)
    with conn.cursor() as cur:
        cur.execute("SELECT legal_name, financials, risk_score FROM atlas_companies")
        assert cur.fetchall() == [("Existing s.r.o.", None, None)]

        cur.execute(
            "UPDATE atlas_companies SET risk_score = 10, financials = %s, last_financial_year = 2024",
            ('{"year": 2024, "template": "687", "history": []}',),
        )
        with pytest.raises(psycopg2.errors.CheckViolation):
            cur.execute("UPDATE atlas_companies SET risk_score = 11")
