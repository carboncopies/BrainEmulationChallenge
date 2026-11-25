#!/usr/bin/env python3
"""Trivial nesfarm job: log in to the API on --port, create a tiny simulation, delete it, report NES RSS-free health.
Standard library only. usage: health_job.py --port 8900 [--user U --password P]"""
import argparse, json, sys, time, urllib.request

def post(url, data, timeout=20):
    r = urllib.request.Request(url, json.dumps(data).encode(), {'Content-Type': 'application/json'})
    with urllib.request.urlopen(r, timeout=timeout) as f:
        return json.loads(f.read().decode())

ap = argparse.ArgumentParser(); ap.add_argument('--port', type=int, required=True)
ap.add_argument('--hold', type=float, default=0, help='seconds to keep the sim before deleting it');
ap.add_argument('--user', default='Admonishing'); ap.add_argument('--password', default='Instruction')
a = ap.parse_args(); base = 'http://127.0.0.1:%d' % a.port
tok = post(base + '/Auth/GetToken', {'Username': a.user, 'Password': a.password})['AuthKey']
nes = lambda q: post('%s/NES?AuthKey=%s' % (base, tok), [dict(q, ReqID=1)])[0]
r = nes({'Simulation/Create': {'Name': 'nesfarm-health'}}); sid = r['SimulationID']
print('created sim', sid, r.get('StatusCode')); time.sleep(a.hold)
t = nes({'Simulation/DeleteResidentByID': {'SimulationID': sid}})
for _ in range(100):
    s = nes({'ManTaskStatus': {'TaskID': t['TaskID']}})
    if s.get('TaskStatus') != 1: break
    time.sleep(0.1)
print('deleted sim', sid, 'TaskStatus', s.get('TaskStatus'))
sys.exit(0 if s.get('TaskStatus') == 0 else 1)
