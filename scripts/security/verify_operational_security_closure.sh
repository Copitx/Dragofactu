#!/usr/bin/env bash
set -euo pipefail

# Quick operational checks for pending security closure items.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

ok=0
warn=0

check_ok() {
  echo "[OK] $1"
  ok=$((ok + 1))
}

check_warn() {
  echo "[WARN] $1"
  warn=$((warn + 1))
}

echo "Running operational security closure checks in: $ROOT_DIR"

# 1) Redis env variable presence (shell context)
if [[ -n "${REDIS_URL:-}" ]]; then
  check_ok "REDIS_URL is set in current shell context."
else
  check_warn "REDIS_URL is not set in current shell context."
fi

# 2) Required security env vars in shell context
for var in SECRET_KEY ALLOWED_ORIGINS METRICS_TOKEN; do
  if [[ -n "${!var:-}" ]]; then
    check_ok "$var is set in current shell context."
  else
    check_warn "$var is not set in current shell context."
  fi
done

# 3) Check for obvious default insecure credentials in tracked files
if command -v rg >/dev/null 2>&1; then
  if rg -n "admin123|dragofactu_dev_only_change_me|dev-secret-key-change-in-production" \
    --glob '!MEMORIA_LARGO_PLAZO.md' \
    --glob '!README*.md' \
    --glob '!docs/**' \
    --glob '!backend/app/core/security_utils.py' \
    --glob '!scripts/security/verify_operational_security_closure.sh' \
    >/tmp/security_closure_scan.txt; then
    check_warn "Found potential insecure defaults in tracked files (review /tmp/security_closure_scan.txt)."
  else
    check_ok "No obvious insecure default credentials found in tracked non-doc files."
  fi
else
  check_warn "rg is not available; skipped insecure default scan."
fi

# 4) Confirm runbook and plan docs exist
for file in \
  "docs/SEGURIDAD_CIERRE_OPERATIVO.md" \
  "PLAN_OPERACIONES_SEGURIDAD.md" \
  "AGENTS.md"; do
  if [[ -f "$file" ]]; then
    check_ok "$file exists."
  else
    check_warn "$file is missing."
  fi
done

echo
echo "Summary: $ok OK, $warn WARN"

if [[ $warn -gt 0 ]]; then
  exit 2
fi

exit 0
