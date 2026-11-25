#!/bin/bash
# start|stop|status instance k.  start: NES then API (each setsid, pids in instances/i<k>/*.pid)
H=$(cd $(dirname $0); pwd); cmd=$1; k=$2; d=$H/instances/i$k; P=$((8200+10*k))
case $cmd in
start) ( cd $d/nes && source /home/johnjose/BrainGenix/BrainGenix-NES/venv/bin/activate && setsid nohup ./BrainGenix-NES >> $d/nes.log 2>&1 & echo $! > $d/nes.pid ); sleep 8
       ( cd $d/api && setsid nohup ./BrainGenix-API >> $d/api.log 2>&1 & echo $! > $d/api.pid ); sleep 5
       ss -ltnp | grep ":$((P+2)) " | grep -o 'pid=[0-9]*' | head -1 | cut -d= -f2 > $d/nes.pid; ss -ltnp | grep "127.0.0.1:$P " | grep -o 'pid=[0-9]*' | head -1 | cut -d= -f2 > $d/api.pid
       echo "i$k NES $(cat $d/nes.pid) API $(cat $d/api.pid) ports $(ss -ltnp | grep -E ":($P|$((P+2))) " | grep -o 'pid=[0-9]*' | tr '\n' ' ')";;
stop) for f in api nes; do p=$(cat $d/$f.pid 2>/dev/null); [ -n "$p" ] && [ "$(readlink /proc/$p/cwd)" = "$d/$f" ] && kill $p && echo "stopped i$k $f $p"; done;;
status) for f in nes api; do p=$(cat $d/$f.pid 2>/dev/null); echo "i$k $f $p rss_kB $(awk '/VmRSS/{print $2}' /proc/$p/status 2>/dev/null)"; done;;
esac
