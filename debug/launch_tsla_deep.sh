#!/usr/bin/env bash
# launch_tsla_deep.sh
# Launcher for TSLA open-scalp deep research Phase 2.
# Runs tsla_deep_research.py and tees output to both stdout and the log file.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-python3}"
RESEARCH_PY="$SCRIPT_DIR/tsla_deep_research.py"
LOG="$SCRIPT_DIR/tsla_deep_loop.log"

echo "========================================"
echo " TSLA Deep Research Phase 2 Launcher"
echo " $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"
echo "Script : $RESEARCH_PY"
echo "Log    : $LOG"
echo ""

# Rotate old log (keep last run)
if [ -f "$LOG" ]; then
    mv "$LOG" "${LOG%.log}_prev.log"
fi

# Run with tee so output goes to both terminal and log
"$PYTHON" "$RESEARCH_PY" 2>&1 | tee "$LOG"

EXIT_CODE=${PIPESTATUS[0]}

echo ""
echo "========================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo " DONE — exit code 0"
else
    echo " FAILED — exit code $EXIT_CODE"
fi
echo "========================================"

exit $EXIT_CODE
