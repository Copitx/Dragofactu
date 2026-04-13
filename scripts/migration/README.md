# Migration Kit (Wave-Based)

This folder contains an executable migration runner to start applying the operational migration plan.

## Files
- `migrate_to_dragofactu.py`: CLI to validate and execute migration waves.
- `extract_from_sqlite.py`: helper to export source SQLite data into migration CSV format.
- `templates/*.csv`: starter CSV templates.

## Supported waves
- `masters`: suppliers, clients, products, workers.
- `operations`: documents + document_lines.
- `diary`: current operational diary entries.
- `all`: masters + operations + diary (if `diary_entries.csv` exists).

## 1) Extract from local SQLite source (optional)
```bash
python scripts/migration/extract_from_sqlite.py \
  --db-path ./dragofactu.db \
  --out-dir ./scripts/migration/input
```

## 2) Generate templates (optional)
```bash
python scripts/migration/migrate_to_dragofactu.py templates --out-dir ./migration_data
```

## 3) Validate data before any write
```bash
python scripts/migration/migrate_to_dragofactu.py validate --data-dir ./migration_data --wave all
```

## 4) Dry-run (no writes)
```bash
python scripts/migration/migrate_to_dragofactu.py run --data-dir ./migration_data --base-url http://localhost:8000 --dry-run --wave all
```

## 5) Real execution
Use an access token with permissions:
- `export.write` (for migration wave execution scope)
- `documents.create` and `documents.update` for operations wave

```bash
python scripts/migration/migrate_to_dragofactu.py run \
  --data-dir ./migration_data \
  --base-url http://localhost:8000 \
  --token "<ACCESS_TOKEN>" \
  --wave all
```

## 6) One-command staged execution (recommended)
The script below enforces: validate -> dry-run -> real waves (`masters`, `operations`, `diary`).

```bash
export TOKEN="<ACCESS_TOKEN>"
export BASE_URL="http://localhost:8000"
export DATA_DIR="$(pwd)/scripts/migration/input"

./scripts/migration/run_staged_migration.sh
```

Run only validation + dry-run (no writes):

```bash
DRY_RUN_ONLY=true ./scripts/migration/run_staged_migration.sh
```

## Expected CSV files in `--data-dir`
- `clients.csv`
- `products.csv`
- `suppliers.csv`
- `workers.csv` (optional but recommended)
- `documents.csv`
- `document_lines.csv`
- `diary_entries.csv` (optional for wave `all`, required for wave `diary`)

## Notes
- The runner is idempotent for masters by `code` (it skips existing codes).
- Documents are created from `documents.csv` and linked to lines by `document_ref`.
- Non-draft statuses are applied through valid transition paths.
- Recommended order in production: `masters` first, then `operations`, then `diary`.
