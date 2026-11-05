#!/bin/bash
# Run the hand-wired Pong controller. Defaults to a local API on port 8000.
# Usage: ./Run.sh [-H host] [-P port] [-m truthtable|play] [-t ticks] [-s seed] [-k tick_ms]
host="localhost"; port="8000"; mode="truthtable"; ticks="500"; seed="1"; tickms="20"
while getopts "H:P:m:t:s:k:" opt; do
  case ${opt} in
    H) host=$OPTARG ;;
    P) port=$OPTARG ;;
    m) mode=$OPTARG ;;
    t) ticks=$OPTARG ;;
    s) seed=$OPTARG ;;
    k) tickms=$OPTARG ;;
    *) echo "Usage: $0 [-H host] [-P port] [-m truthtable|play] [-t ticks] [-s seed] [-k tick_ms]"; exit 1 ;;
  esac
done
cd "$(dirname "$0")"
PY=../../../venv/bin/python
[ -x "$PY" ] || PY=python3
exec $PY pong_handwired.py -Host "$host" -Port "$port" -Mode "$mode" -Ticks "$ticks" -Seed "$seed" -TickMs "$tickms"
