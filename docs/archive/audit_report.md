# Audit Report – V4 Prototype

## Unresolved TODOs

- `backend/services/erp/erp_service.py:153` – Save supplier data to DB or cache.
- Numerous TODO comments in third‑party `passlib` and `stripe` packages (outside project scope).

## Missing Test Coverage

- `services/database.py` – No unit tests for init, session handling, CRUD helpers.
- `services/sk_region_resolver.py` – No tests for CSV loading, fallback mapping, `resolve_region`.
- `services/erp/erp_service.py` – No tests for connector factory, sync logic, or the new cache save.
- `scripts/convert_postal_codes.py` – No tests for CSV conversion logic.
- Overall project lacks a CI script and coverage reporting.

## Suggested Improvements

- Implement the TODO in `erp_service.py` to store supplier data via `save_company_cache`.
- Add a comprehensive test suite covering the above modules.
- Provide a `run_tests.sh` script with coverage reporting.
- Update `README.md` with instructions for running tests.
