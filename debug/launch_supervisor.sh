#!/bin/bash
cd "$(dirname "$0")"
python3 -u autoklb_supervisor.py >> autoklb_loop_run.log 2>&1 &
echo "Supervisor launched, PID=$!"
