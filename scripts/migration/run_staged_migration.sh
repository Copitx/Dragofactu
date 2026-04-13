#!/bin/bash
set -euo pipefail

SCRIPT_PATH="${BASH_SOURCE[0]:-$0}"
SCRIPT_DIR="${SCRIPT_PATH%/*}"
if [[ "$SCRIPT_DIR" == "$SCRIPT_PATH" ]]; then
  SCRIPT_DIR="."
fi

ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

DEFAULT_PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
if [[ ! -x "$DEFAULT_PYTHON_BIN" && -x "$ROOT_DIR/venv/bin/python" ]]; then
  DEFAULT_PYTHON_BIN="$ROOT_DIR/venv/bin/python"
fi

PYTHON_BIN="${PYTHON_BIN:-$DEFAULT_PYTHON_BIN}"
RUNNER="$ROOT_DIR/scripts/migration/migrate_to_dragofactu.py"
DATA_DIR="${DATA_DIR:-$ROOT_DIR/scripts/migration/input}"
BASE_URL="${BASE_URL:-http://localhost:8000}"
TOKEN="${TOKEN:-}"
DRY_RUN_ONLY="${DRY_RUN_ONLY:-false}"

if [[ ! -x "$PYTHON_BIN" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
  else
    echo "ERROR: Python no encontrado (intentado: $PYTHON_BIN, $ROOT_DIR/.venv/bin/python, $ROOT_DIR/venv/bin/python, python3)"
    exit 1
  fi
fi

if [[ ! -f "$RUNNER" ]]; then
  echo "ERROR: Runner no encontrado en $RUNNER"
  exit 1
fi

echo "[1/5] Validando datos de entrada..."
"$PYTHON_BIN" "$RUNNER" validate --data-dir "$DATA_DIR" --wave all

echo "[2/5] Dry-run completo (all)..."
"$PYTHON_BIN" "$RUNNER" run --data-dir "$DATA_DIR" --base-url "$BASE_URL" --dry-run --wave all

if [[ "$DRY_RUN_ONLY" == "true" ]]; then
  echo "DRY_RUN_ONLY=true -> proceso finalizado sin escrituras reales."
  exit 0
fi

if [[ -z "$TOKEN" ]]; then
  echo "ERROR: TOKEN requerido para ejecucion real."
  echo "Tip: export TOKEN='<ACCESS_TOKEN>'"
  exit 1
fi

echo "[3/5] Ejecucion real de maestros..."
"$PYTHON_BIN" "$RUNNER" run --data-dir "$DATA_DIR" --base-url "$BASE_URL" --token "$TOKEN" --wave masters

echo "[4/5] Ejecucion real de operaciones..."
"$PYTHON_BIN" "$RUNNER" run --data-dir "$DATA_DIR" --base-url "$BASE_URL" --token "$TOKEN" --wave operations

echo "[5/5] Ejecucion real de diario..."
"$PYTHON_BIN" "$RUNNER" run --data-dir "$DATA_DIR" --base-url "$BASE_URL" --token "$TOKEN" --wave diary

echo "Migracion por fases completada."
