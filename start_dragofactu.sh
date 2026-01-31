#!/bin/bash
# DRAGOFACTU Final Launcher Script

echo "🐲 DRAGOFACTU - Business Management System"
echo "============================================"

# Ensure we run from the script's directory
cd "$(dirname "$0")"

# Execute the fixed launcher with GUI support
exec python3 launch_dragofactu_fixed.py