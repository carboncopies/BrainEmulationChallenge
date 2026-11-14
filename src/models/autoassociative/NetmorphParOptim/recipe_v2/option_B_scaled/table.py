import json,sys
S=json.load(open('summary.json')); pre=sys.argv[1]
for n,s in S.items():
    if n.startswith(pre) and s['kind']=='ripple':
        print(n.ljust(22),str(s['complete']).ljust(14),'spur',str(s['spurious']).ljust(5),'ct',str(s['crosstalk']).ljust(3),'pyr',str(s['pyr_spikes']).ljust(5),'int',str(s['int_total']).ljust(4),'bend',s['burst_end'],'last',s['last'],'OK' if s['success'] else 'fail')
