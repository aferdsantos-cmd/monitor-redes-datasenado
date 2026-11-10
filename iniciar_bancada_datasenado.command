#!/usr/bin/env bash
# ==============================================================================
# Atalho 1-Click macOS para Finder: Bancada Analítica DataSenado 360º
# ==============================================================================
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${DIR}"

exec bash "${DIR}/scripts/run_workbench_360.sh"
