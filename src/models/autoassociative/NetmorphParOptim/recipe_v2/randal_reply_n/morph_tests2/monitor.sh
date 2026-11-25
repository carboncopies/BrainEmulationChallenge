#!/bin/bash
# Resource monitor (every 60 s) for morph_tests: load, cpu/iowait, disk util, RSS of our NES/API instances, total used RAM.
# Writes monitor.log (TSV). Flags STOP_NEW if used RAM > 240 GB. Ends when no batch_i*/run.log is still running (no run_batch.py process).
H=$(cd $(dirname $0); pwd); cd $H
echo -e "time\tload1\tcpu_us\tcpu_sy\tcpu_wa\tcpu_id\tdisk_util%\tdisk_wMBs\tused_GB\tour_nes_rss_GB\tour_cpu%\tper_inst_rss_GB" >> monitor.log
while true; do
  v=$(vmstat 5 2 | tail -1); us=$(echo $v | awk '{print $13}'); sy=$(echo $v | awk '{print $14}'); id=$(echo $v | awk '{print $15}'); wa=$(echo $v | awk '{print $16}')
  io=$(iostat -dx sda 5 2 | awk '/^sda/{u=$NF; w=$9} END{print u"\t"w/1024}')
  used=$(free -g | awk '/Mem:/{print $3}')
  tot=0; cpu=0; per=""
  for d in instances/i*; do p=$(cat $d/nes.pid 2>/dev/null); r=$(awk '/VmRSS/{print $2}' /proc/$p/status 2>/dev/null); r=${r:-0}
    c=$(ps -o %cpu= -p $p 2>/dev/null | tr -d ' '); c=${c:-0}; tot=$((tot+r)); cpu=$(echo "$cpu+$c" | bc); per="$per $(basename $d):$(echo "scale=1;$r/1048576" | bc)"
    [ $r -gt 10485760 ] && echo "$(date +%T) $(basename $d) RSS > 10 GB" >> monitor_flags.log; done
  echo -e "$(date +%T)\t$(cut -d' ' -f1 /proc/loadavg)\t$us\t$sy\t$wa\t$id\t$io\t$used\t$(echo "scale=1;$tot/1048576" | bc)\t$cpu\t$per" >> monitor.log
  [ $used -gt 240 ] && touch STOP_NEW && echo "$(date +%T) used RAM $used GB > 240: STOP_NEW" >> monitor_flags.log
  pgrep -f '[r]un_instance.py' > /dev/null || { echo "$(date +%T) no batch running, monitor ends" >> monitor_flags.log; break; }
  sleep 50
done
