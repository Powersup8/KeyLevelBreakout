#!/bin/bash
cd "$(dirname "$0")"
python3 -u tsla_research_loop.py >> tsla_research_loop.log 2>&1 &
echo "TSLA research launched, PID=$!"
