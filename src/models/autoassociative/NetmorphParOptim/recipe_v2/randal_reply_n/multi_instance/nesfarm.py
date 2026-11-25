#!/usr/bin/env python3
"""nesfarm: run several independent NES+API instances side by side and feed them jobs.

Python 3 standard library only. Subcommands: up, status, run, guard, down, clean, restart.
State lives in <farm_root>/<tag>/ (state.json, events.log, instance folders, job logs).
Every process this tool stops must be recorded in its own tag's state.json, with a matching
start time and working directory, and must not be a protected PID. See README.md.
"""
import argparse, contextlib, fcntl, json, os, re, shlex, signal, socket, subprocess, sys, time
import urllib.request, urllib.error

PKG = os.path.dirname(os.path.abspath(__file__))
TAG_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.-]{0,31}$')
CLK = os.sysconf('SC_CLK_TCK')
PAGE_KB = os.sysconf('SC_PAGE_SIZE') // 1024

DEFAULTS = {
    "farm_root": "${NESFARM_ROOT:-~/.local/state/nesfarm}",
    "api_binary": "${NESFARM_API_BINARY:-}",          # BrainGenix-API executable
    "users_json": "${NESFARM_USERS_JSON:-}",          # Source/Core/Config/users.json for the API
    "nes_venv": "${NESFARM_NES_VENV:-}",              # optional venv activated for NES (as the old inst.sh did)
    "api_user": "${NESFARM_API_USER:-Admonishing}",   # local dev credentials used by the BEC scripts
    "api_password": "${NESFARM_API_PASSWORD:-Instruction}",
    "max_cores": 48,               # cap on cores used by ALL nesfarm processes (all tags: NES, API, jobs)
    "max_ram_gb": 250,             # cap on machine-wide used RAM (MemTotal - MemAvailable)
    "rss_restart_gb": 10,          # restart an instance above this NES RSS, only when idle
    "max_jobs_per_instance": 3,    # job slots per instance (a 3-growth batch uses 3 slots)
    "est_ram_gb_per_instance": 3,  # used by `up` to check the RAM cap before starting
    "est_cores_per_instance": 2,   # an idle NES burns ~2 cores
    "port_stride": 10,             # instance k uses base + stride*k .. +4
    "protected_pids": [3156209, 1972355],
    "job_stagger_s": 5,
    "start_timeout_s": 90,
    "nes_yaml": {"Network_NES_API_Host": "0.0.0.0", "VSDA_EM_PercentOfSysteMemoryLimit": 70,
                 "VSDA_EM_MaxVoxelArraySize": 5000},
    "default_job_env": {"OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"},
}

# ------------------------------------------------------------------ config


def _expand(v):
    if not isinstance(v, str):
        return v
    def sub(m):
        name, dflt = m.group(1), m.group(2)
        return os.environ.get(name) or (dflt or '')
    v = re.sub(r'\$\{([A-Z0-9_]+)(?::-([^}]*))?\}', sub, v)
    return os.path.expanduser(os.path.expandvars(v))


def load_config(path=None):
    cfg = json.loads(json.dumps(DEFAULTS))
    xdg = os.environ.get('XDG_CONFIG_HOME') or os.path.expanduser('~/.config')
    cands = [path, os.environ.get('NESFARM_CONFIG'), os.path.join(os.getcwd(), 'nesfarm.json'),
             os.path.join(xdg, 'nesfarm.json'), os.path.join(PKG, 'nesfarm.json')]
    used = None
    for c in cands:
        if c and os.path.isfile(c):
            with open(c) as f:
                user = json.load(f)
            for k, v in user.items():
                if k.startswith('_'):
                    continue
                if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                    cfg[k].update(v)
                else:
                    cfg[k] = v
            used = c
            break
    if path and used != path:
        sys.exit('config file not found: %s' % path)
    for k in ('max_cores', 'max_ram_gb', 'rss_restart_gb', 'max_jobs_per_instance'):
        e = os.environ.get('NESFARM_' + k.upper())
        if e:
            cfg[k] = float(e) if '.' in e else int(e)
    for k in list(cfg):
        cfg[k] = _expand(cfg[k])
    cfg['farm_root'] = os.path.abspath(cfg['farm_root'])
    cfg['protected_pids'] = set(int(p) for p in cfg['protected_pids'])
    cfg['_config_file'] = used
    return cfg

# ------------------------------------------------------------------ /proc helpers


def proc_stat(pid):
    try:
        with open('/proc/%d/stat' % pid) as f:
            s = f.read()
    except (FileNotFoundError, ProcessLookupError, PermissionError):
        return None
    rest = s[s.rindex(')') + 2:].split()
    # rest[0] = state (field 3); utime=14, stime=15, ppid=4, starttime=22 (1-based fields)
    return {'state': rest[0], 'ppid': int(rest[1]), 'utime': int(rest[11]), 'stime': int(rest[12]),
            'starttime': int(rest[19]), 'threads': int(rest[17])}


def pid_alive(pid):
    st = proc_stat(pid) if pid else None
    return st is not None and st['state'] != 'Z'


def proc_cwd(pid):
    try:
        return os.path.realpath(os.readlink('/proc/%d/cwd' % pid))
    except OSError:
        return None


def rss_kb(pid):
    try:
        with open('/proc/%d/status' % pid) as f:
            for line in f:
                if line.startswith('VmRSS'):
                    return int(line.split()[1])
    except OSError:
        pass
    return 0


def children_map():
    kids = {}
    for d in os.listdir('/proc'):
        if d.isdigit():
            st = proc_stat(int(d))
            if st:
                kids.setdefault(st['ppid'], []).append(int(d))
    return kids


def tree(pids, kids=None):
    kids = kids if kids is not None else children_map()
    out, stack = set(), list(pids)
    while stack:
        p = stack.pop()
        if p in out:
            continue
        out.add(p)
        stack.extend(kids.get(p, []))
    return out


def cpu_cores(pids, window=1.0):
    """Cores used by the given pids over `window` seconds."""
    def ticks():
        t = 0
        for p in pids:
            st = proc_stat(p)
            if st:
                t += st['utime'] + st['stime']
        return t
    a = ticks(); time.sleep(window); b = ticks()
    return max(0.0, (b - a) / CLK / window)


def machine_mem():
    m = {}
    with open('/proc/meminfo') as f:
        for line in f:
            k, v = line.split(':')
            m[k] = int(v.split()[0])
    tot, avail = m['MemTotal'] / 1048576, m['MemAvailable'] / 1048576
    return tot, tot - avail


def loadavg():
    with open('/proc/loadavg') as f:
        return float(f.read().split()[0])


def port_free(port):
    for host in ('0.0.0.0', '127.0.0.1'):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((host, port))
        except OSError:
            return False
        finally:
            s.close()
    return True


def port_listening(port):
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.settimeout(1)
        return s.connect_ex(('127.0.0.1', port)) == 0

# ------------------------------------------------------------------ state


class Farm:
    def __init__(self, cfg, tag, dry=False):
        if not TAG_RE.match(tag or ''):
            sys.exit('bad tag %r (letters, digits, _ . -; max 32)' % tag)
        self.cfg, self.tag, self.dry = cfg, tag, dry
        self.dir = os.path.join(cfg['farm_root'], tag)
        self.state_path = os.path.join(self.dir, 'state.json')

    def exists(self):
        return os.path.isfile(self.state_path)

    def load(self):
        with open(self.state_path) as f:
            return json.load(f)

    def save(self, st):
        if self.dry:
            return
        tmp = self.state_path + '.tmp'
        with open(tmp, 'w') as f:
            json.dump(st, f, indent=1)
        os.replace(tmp, self.state_path)

    @contextlib.contextmanager
    def lock(self):
        if self.dry or not os.path.isdir(self.dir):
            yield; return
        with open(os.path.join(self.dir, 'state.lock'), 'a') as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

    def log(self, msg):
        line = '%s [%s] %s' % (time.strftime('%F %T'), self.tag, msg)
        print(line, flush=True)
        if not self.dry and os.path.isdir(self.dir):
            with open(os.path.join(self.dir, 'events.log'), 'a') as f:
                f.write(line + '\n')

    def runner_pid(self):
        p = os.path.join(self.dir, 'run.lock')
        try:
            pid = int(open(p).read().split()[0])
        except (OSError, ValueError, IndexError):
            return None
        return pid if pid_alive(pid) else None

    def running_jobs(self):
        try:
            with open(os.path.join(self.dir, 'running.json')) as f:
                d = json.load(f)
            if self.runner_pid():
                return {int(k): v for k, v in d.items()}
        except (OSError, ValueError):
            pass
        return {}


def all_tags(cfg):
    r = cfg['farm_root']
    if not os.path.isdir(r):
        return []
    return sorted(t for t in os.listdir(r) if os.path.isfile(os.path.join(r, t, 'state.json')))


def all_farm_pids(cfg):
    """NES/API pids of every tag, plus job process trees of active runners."""
    pids = set()
    for t in all_tags(cfg):
        f = Farm(cfg, t)
        try:
            st = f.load()
        except (OSError, ValueError):
            continue
        for inst in st['instances']:
            for role in ('nes', 'api'):
                if verify_own(cfg, f, inst, role, quiet=True):
                    pids.add(inst[role + '_pid'])
        rp = f.runner_pid()
        if rp:
            pids |= tree([rp])
    return pids


def reserved_ports(cfg, except_tag=None):
    res = {}
    for t in all_tags(cfg):
        if t == except_tag:
            continue
        try:
            st = Farm(cfg, t).load()
        except (OSError, ValueError):
            continue
        if not any(i.get('nes_pid') or i.get('api_pid') for i in st['instances']):
            continue
        for inst in st['instances']:
            for p in range(inst['api_port'], inst['api_port'] + 5):
                res[p] = t
    return res


def verify_own(cfg, farm, inst, role, quiet=False):
    """True only if the pid recorded for this role is alive, not protected, started at the recorded
    time and runs in the recorded instance folder of this tag."""
    pid = inst.get(role + '_pid')
    why = None
    if not pid:
        why = 'no pid recorded'
    elif pid in cfg['protected_pids']:
        why = 'PROTECTED pid %d' % pid
    else:
        st = proc_stat(pid)
        if st is None or st['state'] == 'Z':
            why = 'not running'
        elif st['starttime'] != inst.get(role + '_starttime'):
            why = 'pid %d reused by another process (start time differs)' % pid
        else:
            want = os.path.realpath(os.path.join(inst['dir'], role))
            if proc_cwd(pid) != want:
                why = 'pid %d cwd %s != %s' % (pid, proc_cwd(pid), want)
            elif not want.startswith(os.path.realpath(farm.dir) + os.sep):
                why = 'instance dir outside tag dir'
    if why and not quiet:
        farm.log('i%d %s: %s' % (inst['k'], role, why))
    return why is None

# ------------------------------------------------------------------ HTTP (API) helpers


def http_json(url, data=None, timeout=10):
    req = urllib.request.Request(url, data=None if data is None else json.dumps(data).encode(),
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode() or 'null')


def health(port, timeout=5):
    """Returns (ok, detail). API /Hello and /Diagnostic/Version."""
    base = 'http://127.0.0.1:%d' % port
    try:
        urllib.request.urlopen(base + '/Hello', timeout=timeout).read()
        v = http_json(base + '/Diagnostic/Version', timeout=timeout)
        if isinstance(v, dict) and v.get('StatusCode', 1) == 0:
            return True, 'NES-API %s' % v.get('NESAPIVersion', v.get('Version', '?'))
        return False, 'version reply %s' % str(v)[:80]
    except Exception as e:
        return False, '%s' % (str(e)[:80] or type(e).__name__)


class Api:
    def __init__(self, cfg, port):
        self.base = 'http://127.0.0.1:%d' % port
        r = http_json(self.base + '/Auth/GetToken', {'Username': cfg['api_user'], 'Password': cfg['api_password']})
        if not isinstance(r, dict) or r.get('StatusCode') != 0:
            raise RuntimeError('login failed: %s' % str(r)[:120])
        self.token, self.req = r['AuthKey'], 0

    def nes(self, query, timeout=30):
        self.req += 1
        q = dict(query, ReqID=self.req)
        return http_json('%s/NES?AuthKey=%s' % (self.base, self.token), [q], timeout=timeout)[0]

    def managed(self, query, timeout=60):
        r = self.nes(query)
        if not isinstance(r, dict) or 'TaskID' not in r:
            return False, r
        t0 = time.time()
        while time.time() - t0 < timeout:
            s = self.nes({'ManTaskStatus': {'TaskID': r['TaskID']}})
            if isinstance(s, dict) and s.get('StatusCode') == 0 and s.get('TaskStatus') != 1:
                return s.get('TaskStatus') == 0, s
            time.sleep(0.2)
        return False, 'timeout'

# ------------------------------------------------------------------ instance lifecycle


def find_binaries(build):
    for d in (os.path.join(build, 'Binaries'), build):
        if os.path.isfile(os.path.join(d, 'BrainGenix-NES')):
            return os.path.abspath(d)
    sys.exit('no BrainGenix-NES in %s or %s/Binaries' % (build, build))


def write_nes_yaml(src, dst, nes_port, out_dir, extra):
    keys = dict(extra, Network_NES_API_Port=nes_port, Output_BasePath=out_dir)
    lines, seen = [], set()
    if os.path.isfile(src):
        for line in open(src):
            m = re.match(r'^([A-Za-z0-9_]+)\s*:', line)
            if m and m.group(1) in keys:
                lines.append('%s: %s\n' % (m.group(1), keys[m.group(1)])); seen.add(m.group(1))
            else:
                lines.append(line if line.endswith('\n') else line + '\n')
    for k, v in keys.items():
        if k not in seen:
            lines.append('%s: %s\n' % (k, v))
    with open(dst, 'w') as f:
        f.writelines(lines)


API_CFG = """[Network.Service]
Port={P}
Host=127.0.0.1
UseHTTPS=False
KeyFilePath=SetYourPathHere
CrtFilePath=SetYourPathHere
URL=localhost

[Network.RPCCallback]
Port={P1}
Host=localhost

[Network.NES]
Port={P2}
Host=localhost
Timeout_ms=10000

[Network.EVM]
Port={P3}
Host=localhost
Timeout_ms=10000

[Network.Neuroglancer]
Port={P4}
"""


def make_instance_dir(cfg, farm, k, bins, api_port, link_models):
    d = os.path.join(farm.dir, 'i%d' % k)
    nes, api, out = os.path.join(d, 'nes'), os.path.join(d, 'api'), os.path.join(d, 'out')
    for x in (nes, api, out, os.path.join(d, 'Source', 'Core', 'Config'), os.path.join(out, cfg['api_user'], 'Models')):
        os.makedirs(x, exist_ok=True)
    for f in os.listdir(bins):
        if f == 'NES.yaml':
            continue
        dst = os.path.join(nes, f)
        if not os.path.lexists(dst):
            os.symlink(os.path.join(bins, f), dst)
    write_nes_yaml(os.path.join(bins, 'NES.yaml'), os.path.join(nes, 'NES.yaml'), api_port + 2, out, cfg['nes_yaml'])
    dst = os.path.join(api, 'BrainGenix-API')
    if not os.path.lexists(dst):
        os.symlink(os.path.abspath(cfg['api_binary']), dst)
    with open(os.path.join(api, 'API.cfg'), 'w') as f:
        f.write(API_CFG.format(P=api_port, P1=api_port + 1, P2=api_port + 2, P3=api_port + 3, P4=api_port + 4))
    # The API reads ../Source/Core/Config/users.json relative to its cwd (else "Service unavailable").
    with open(cfg['users_json']) as a, open(os.path.join(d, 'Source', 'Core', 'Config', 'users.json'), 'w') as b:
        b.write(a.read())
    for m in link_models:
        dst = os.path.join(out, cfg['api_user'], 'Models', os.path.basename(m.rstrip('/')))
        if not os.path.lexists(dst):
            os.symlink(os.path.abspath(m), dst)
    return d


def spawn(cmd, cwd, log, env=None):
    with open(log, 'a') as lf:
        p = subprocess.Popen(cmd, cwd=cwd, stdout=lf, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                             env=env, start_new_session=True)
    return p.pid, proc_stat(p.pid)['starttime']


def start_instance(cfg, farm, st, inst):
    """Start NES then API for one instance; records pids in state as soon as each starts."""
    P = inst['api_port']
    for p in range(P, P + 5):
        t0 = time.time()
        while not port_free(p) and time.time() - t0 < 30:
            time.sleep(1)
        if not port_free(p):
            raise RuntimeError('port %d in use' % p)
    env = dict(os.environ)
    if cfg['nes_venv']:
        env['VIRTUAL_ENV'] = cfg['nes_venv']; env['PATH'] = os.path.join(cfg['nes_venv'], 'bin') + ':' + env['PATH']
    d = inst['dir']
    inst['nes_pid'], inst['nes_starttime'] = spawn(['./BrainGenix-NES'], os.path.join(d, 'nes'), os.path.join(d, 'nes.log'), env)
    farm.save(st)
    t0 = time.time()
    while not port_listening(P + 2):
        if not pid_alive(inst['nes_pid']):
            raise RuntimeError('i%d NES exited at start (see %s/nes.log)' % (inst['k'], d))
        if time.time() - t0 > cfg['start_timeout_s']:
            raise RuntimeError('i%d NES not listening on %d' % (inst['k'], P + 2))
        time.sleep(1)
    inst['api_pid'], inst['api_starttime'] = spawn(['./BrainGenix-API'], os.path.join(d, 'api'), os.path.join(d, 'api.log'))
    farm.save(st)
    t0 = time.time()
    while True:
        ok, detail = health(P, timeout=3)
        if ok:
            break
        if not pid_alive(inst['api_pid']):
            raise RuntimeError('i%d API exited at start (see %s/api.log)' % (inst['k'], d))
        if time.time() - t0 > cfg['start_timeout_s']:
            raise RuntimeError('i%d API not healthy on %d: %s' % (inst['k'], P, detail))
        time.sleep(1)
    inst['started'] = time.strftime('%F %T')
    farm.save(st)
    farm.log('i%d up: NES pid %d (port %d), API pid %d (port %d), %s' % (inst['k'], inst['nes_pid'], P + 2, inst['api_pid'], P, detail))


def safe_kill(cfg, farm, inst, role, timeout=30):
    pid = inst.get(role + '_pid')
    if not pid:
        return True
    if pid in cfg['protected_pids']:
        farm.log('REFUSED to stop protected pid %d' % pid); return False
    if not verify_own(cfg, farm, inst, role):
        if not pid_alive(pid):
            inst[role + '_pid'] = None; return True
        farm.log('REFUSED to stop pid %d: not verified as this tag\'s %s' % (pid, role)); return False
    if farm.dry:
        farm.log('[dry-run] would stop i%d %s pid %d' % (inst['k'], role, pid)); return True
    os.kill(pid, signal.SIGTERM)
    t0 = time.time()
    while pid_alive(pid) and time.time() - t0 < timeout:
        time.sleep(0.5)
    if pid_alive(pid):
        if verify_own(cfg, farm, inst, role, quiet=True):
            os.kill(pid, signal.SIGKILL); time.sleep(1)
    gone = not pid_alive(pid)
    farm.log('i%d %s pid %d %s' % (inst['k'], role, pid, 'stopped' if gone else 'STILL RUNNING'))
    if gone:
        inst[role + '_pid'] = None
    return gone


def stop_instance(cfg, farm, st, inst):
    ok = safe_kill(cfg, farm, inst, 'api') and safe_kill(cfg, farm, inst, 'nes')
    farm.save(st)
    return ok


def restart_instance(cfg, farm, k, reason):
    with farm.lock():
        st = farm.load()
        inst = st['instances'][k]
        farm.log('i%d restart: %s' % (k, reason))
        if farm.dry:
            return True
        if not stop_instance(cfg, farm, st, inst):
            farm.log('i%d restart aborted: could not stop own processes' % k); return False
        try:
            start_instance(cfg, farm, st, inst)
        except RuntimeError as e:
            farm.log('i%d restart FAILED: %s' % (k, e)); return False
        inst['restarts'] = inst.get('restarts', 0) + 1
        farm.save(st)
        return True

# ------------------------------------------------------------------ caps


def cap_check(cfg, extra_cores=0.0, extra_ram=0.0, window=1.0):
    """Returns (ok, message, numbers)."""
    tot, used = machine_mem()
    pids = all_farm_pids(cfg)
    cores = cpu_cores(pids, window) if pids else 0.0
    msgs = []
    if used + extra_ram > cfg['max_ram_gb']:
        msgs.append('machine used RAM %.0f GB (+%.0f) > cap %s GB' % (used, extra_ram, cfg['max_ram_gb']))
    if cores + extra_cores > cfg['max_cores']:
        msgs.append('nesfarm cores %.1f (+%.0f) > cap %s' % (cores, extra_cores, cfg['max_cores']))
    stop = os.path.join(cfg['farm_root'], 'STOP_NEW')
    if os.path.exists(stop):
        msgs.append('STOP_NEW present (%s)' % open(stop).read().strip()[:100])
    return not msgs, '; '.join(msgs), dict(used_ram_gb=used, total_ram_gb=tot, farm_cores=cores, load1=loadavg())

# ------------------------------------------------------------------ commands


def cmd_up(cfg, a):
    farm = Farm(cfg, a.tag, a.dry_run)
    if farm.exists():
        st = farm.load()
        live = [i['k'] for i in st['instances'] if pid_alive(i.get('nes_pid') or 0) or pid_alive(i.get('api_pid') or 0)]
        if live:
            sys.exit('tag %s already has running instances %s; use `down --tag %s` first' % (a.tag, live, a.tag))
    for need in ('api_binary', 'users_json'):
        if not cfg[need] or not os.path.isfile(cfg[need]):
            sys.exit('config %s not set or missing: %r (set it in nesfarm.json or NESFARM_%s)' % (need, cfg[need], need.upper()))
    bins = find_binaries(a.build)
    n, base, stride = a.n, a.base_port, cfg['port_stride']
    if stride < 5:
        sys.exit('port_stride must be >= 5')
    other = reserved_ports(cfg, except_tag=a.tag)
    bad = []
    for k in range(n):
        for p in range(base + stride * k, base + stride * k + 5):
            if p in other:
                bad.append('%d (tag %s)' % (p, other[p]))
            elif not port_free(p):
                bad.append('%d (in use)' % p)
    if bad:
        sys.exit('ports not available: %s' % ', '.join(bad))
    ok, msg, num = cap_check(cfg, extra_cores=n * cfg['est_cores_per_instance'], extra_ram=n * cfg['est_ram_gb_per_instance'])
    print('machine: used RAM %.0f/%.0f GB, load %.1f, nesfarm cores %.1f' % (num['used_ram_gb'], num['total_ram_gb'], num['load1'], num['farm_cores']))
    if not ok:
        sys.exit('refusing to start: ' + msg)
    for m in a.link_model or []:
        if not os.path.exists(m):
            sys.exit('model to link not found: %s' % m)
    plan = [(k, base + stride * k) for k in range(n)]
    if a.dry_run:
        for k, P in plan:
            print('[dry-run] i%d: API %d, callback %d, NES %d, EVM %d, neuroglancer %d; dir %s/i%d; build %s'
                  % (k, P, P + 1, P + 2, P + 3, P + 4, farm.dir, k, bins))
        return
    os.makedirs(farm.dir, exist_ok=True)
    st = {'tag': a.tag, 'build': bins, 'base_port': base, 'created': time.strftime('%F %T'),
          'config_file': cfg['_config_file'], 'instances': []}
    for k, P in plan:
        d = make_instance_dir(cfg, farm, k, bins, P, a.link_model or [])
        st['instances'].append({'k': k, 'dir': d, 'api_port': P, 'nes_port': P + 2,
                                'nes_pid': None, 'api_pid': None, 'restarts': 0})
    farm.save(st)
    farm.log('up: %d instances from %s, ports %d..%d' % (n, bins, base, base + stride * (n - 1) + 4))
    failed = False
    with farm.lock():
        for inst in st['instances']:
            try:
                start_instance(cfg, farm, st, inst)
            except RuntimeError as e:
                farm.log('FAILED: %s' % e); failed = True; break
            time.sleep(2)
    if failed:
        farm.log('stopping what this call started')
        for inst in st['instances']:
            stop_instance(cfg, farm, st, inst)
        sys.exit(1)
    print('ok: tag %s up; state %s' % (a.tag, farm.state_path))


def cmd_status(cfg, a):
    tags = [a.tag] if a.tag else all_tags(cfg)
    tot, used = machine_mem()
    print('machine: load %.1f, used RAM %.0f/%.0f GB; caps: %s cores (nesfarm), %s GB (machine)'
          % (loadavg(), used, tot, cfg['max_cores'], cfg['max_ram_gb']))
    if os.path.exists(os.path.join(cfg['farm_root'], 'STOP_NEW')):
        print('STOP_NEW: ' + open(os.path.join(cfg['farm_root'], 'STOP_NEW')).read().strip())
    if not tags:
        print('no tags in %s' % cfg['farm_root']); return
    for t in tags:
        farm = Farm(cfg, t)
        if not farm.exists():
            print('tag %s: no state' % t); continue
        st = farm.load()
        rp, running = farm.runner_pid(), farm.running_jobs()
        print('\ntag %s  build %s  runner %s' % (t, st['build'], rp or '-'))
        pids = []
        rows = []
        for inst in st['instances']:
            vn, va = verify_own(cfg, farm, inst, 'nes', True), verify_own(cfg, farm, inst, 'api', True)
            ok, det = health(inst['api_port'], 3) if (vn and va) else (False, 'down')
            np_ = inst.get('nes_pid')
            if vn:
                pids.append(np_)
            rows.append((inst, vn, va, ok, det))
        cores = {}
        if pids:
            for p in pids:
                cores[p] = 0.0
            a0 = {p: (proc_stat(p) or {'utime': 0, 'stime': 0}) for p in pids}
            time.sleep(1)
            for p in pids:
                b = proc_stat(p)
                if b:
                    cores[p] = (b['utime'] + b['stime'] - a0[p]['utime'] - a0[p]['stime']) / CLK
        print('  %-3s %-6s %-9s %-9s %7s %7s %6s %-5s %s' % ('k', 'API', 'NES pid', 'API pid', 'RSS GB', 'threads', 'cores', 'jobs', 'health'))
        for inst, vn, va, ok, det in rows:
            np_ = inst.get('nes_pid')
            s = proc_stat(np_) if vn else None
            print('  i%-2d %-6d %-9s %-9s %7.1f %7s %6.1f %-5s %s' % (
                inst['k'], inst['api_port'], np_ if vn else '-', inst.get('api_pid') if va else '-',
                rss_kb(np_) / 1048576 if vn else 0, s['threads'] if s else '-', cores.get(np_, 0.0),
                len(running.get(inst['k'], [])), ('ok ' if ok else 'DOWN ') + det))


def cmd_down(cfg, a):
    farm = Farm(cfg, a.tag, a.dry_run)
    if not farm.exists():
        sys.exit('no state for tag %s' % a.tag)
    if farm.runner_pid() and not a.force:
        sys.exit('a runner (pid %d) is active on tag %s; stop it first or pass --force' % (farm.runner_pid(), a.tag))
    with farm.lock():
        st = farm.load()
        ok = True
        for inst in st['instances']:
            if a.k is not None and inst['k'] != a.k:
                continue
            ok &= stop_instance(cfg, farm, st, inst)
    if not ok:
        sys.exit('some processes were not stopped (see above)')
    print('ok: tag %s down%s' % (a.tag, ' (dry-run)' if a.dry_run else ''))


def cmd_restart(cfg, a):
    farm = Farm(cfg, a.tag, a.dry_run)
    if farm.running_jobs().get(a.k) and not a.force:
        sys.exit('i%d has running jobs; pass --force to restart anyway' % a.k)
    sys.exit(0 if restart_instance(cfg, farm, a.k, 'manual') else 1)


def cmd_clean(cfg, a):
    farm = Farm(cfg, a.tag, a.dry_run)
    if farm.runner_pid() and not a.force:
        sys.exit('a runner is active on tag %s (its jobs may own sims); pass --force to clean anyway' % a.tag)
    st = farm.load()
    ids = [int(x) for x in a.ids.split(',')] if a.ids else list(range(a.max_id + 1))
    for inst in st['instances']:
        if a.k is not None and inst['k'] != a.k:
            continue
        if a.restart:
            restart_instance(cfg, farm, inst['k'], 'clean --restart (drops all resident sims and leaked RSS)')
            continue
        if not (verify_own(cfg, farm, inst, 'nes', True) and verify_own(cfg, farm, inst, 'api', True)):
            farm.log('i%d not running, skipped' % inst['k']); continue
        if a.dry_run:
            farm.log('[dry-run] i%d would try DeleteResidentByID for %d ids' % (inst['k'], len(ids))); continue
        api, deleted = Api(cfg, inst['api_port']), []
        for sid in ids:
            ok, _ = api.managed({'Simulation/DeleteResidentByID': {'SimulationID': sid}}, timeout=a.timeout)
            if ok:
                deleted.append(sid)
        farm.log('i%d clean: deleted %d resident sims %s; RSS now %.1f GB' % (
            inst['k'], len(deleted), deleted[:20], rss_kb(inst['nes_pid']) / 1048576))


def _fmt(s, ctx):
    """Fill {placeholders}, then expand $ENV_VARS (use {{ }} for literal braces)."""
    try:
        return os.path.expandvars(s.format(**ctx))
    except KeyError as e:
        sys.exit('unknown placeholder %s in %r; known: %s' % (e, s, ', '.join(sorted(ctx))))


def load_jobs(path):
    with open(path) as f:
        jf = json.load(f)
    dflt = jf.get('defaults', {})
    jobs, names = [], set()
    for i, raw in enumerate(jf['jobs']):
        j = dict(dflt, **raw)
        j.setdefault('name', 'job%03d' % i)
        if not TAG_RE.match(j['name']):
            sys.exit('bad job name %r' % j['name'])
        if j['name'] in names:
            sys.exit('duplicate job name %s' % j['name'])
        names.add(j['name'])
        j['env'] = dict(dflt.get('env', {}), **raw.get('env', {}))
        j['slots'] = int(j.get('slots', 1))
        jobs.append(j)
    return jobs


def cmd_run(cfg, a):
    farm = Farm(cfg, a.tag, a.dry_run)
    if not farm.exists():
        sys.exit('no state for tag %s; run `up` first' % a.tag)
    jobs = load_jobs(a.job_file)
    maxper = a.max_per_instance or cfg['max_jobs_per_instance']
    for j in jobs:
        if j['slots'] > maxper:
            sys.exit('job %s needs %d slots > max per instance %d' % (j['name'], j['slots'], maxper))
    if a.detach and not a.dry_run:
        log = os.path.join(farm.dir, 'run.log')
        argv = [sys.executable, os.path.abspath(__file__)] + [x for x in sys.argv[1:] if x != '--detach']
        with open(log, 'a') as lf:
            p = subprocess.Popen(argv, stdout=lf, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
        print('runner detached: pid %d, log %s' % (p.pid, log)); return
    st = farm.load()
    insts = [i['k'] for i in st['instances'] if a.instances is None or i['k'] in a.instances]
    jdir = os.path.join(farm.dir, 'jobs')

    def ctx(j, inst):
        return dict(host='127.0.0.1', port=inst['api_port'], nes_port=inst['nes_port'], instance=inst['k'], tag=a.tag,
                    name=j['name'], job_dir=os.path.join(jdir, j['name']), farm_dir=farm.dir, out_dir=os.path.join(inst['dir'], 'out'))

    def done_ok(j):
        try:
            return json.load(open(os.path.join(jdir, j['name'], 'status.json'))).get('rc') == 0
        except (OSError, ValueError):
            return False

    pending = [j for j in jobs if a.rerun or not done_ok(j)]
    skipped = len(jobs) - len(pending)
    if a.dry_run:
        load, disp = {k: 0 for k in insts}, {k: 0 for k in insts}
        for j in pending:   # plan as if no job finished; when all slots are full, start the next wave
            k = min((k for k in insts if load[k] + j['slots'] <= maxper), key=lambda k: (load[k], disp[k], k), default=None)
            if k is None:
                load = {k: 0 for k in insts}
                k = min(insts, key=lambda k: (disp[k], k))
            load[k] += j['slots']; disp[k] += 1
            inst = st['instances'][k]
            cx = ctx(j, inst)
            c = _fmt(j['cmd'], cx) if isinstance(j['cmd'], str) else ' '.join(shlex.quote(_fmt(x, cx)) for x in j['cmd'])
            print('[dry-run] %s -> i%d (port %d, %d slot%s): %s' % (j['name'], k, inst['api_port'], j['slots'], 's' * (j['slots'] > 1), c))
        print('[dry-run] %d jobs, %d already done (skipped), max %d slots per instance on %d instances' % (len(pending), skipped, maxper, len(insts)))
        return

    lockp = os.path.join(farm.dir, 'run.lock')
    if farm.runner_pid():
        sys.exit('another runner (pid %d) holds tag %s' % (farm.runner_pid(), a.tag))
    with open(lockp, 'w') as f:
        f.write('%d %s\n' % (os.getpid(), a.job_file))
    os.makedirs(jdir, exist_ok=True)
    running = {}  # name -> dict(proc, k, slots, t0, timeout)
    dispatched = {k: 0 for k in insts}  # tie-break: spread jobs (and the per-sim RSS leak) evenly
    stopping = {'flag': False}

    def on_sig(signum, frame):
        stopping['flag'] = True
    signal.signal(signal.SIGTERM, on_sig); signal.signal(signal.SIGINT, on_sig)

    def write_running():
        d = {k: [n for n, r in running.items() if r['k'] == k] for k in insts}
        with open(os.path.join(farm.dir, 'running.json'), 'w') as f:
            json.dump(d, f)

    def slots_on(k):
        return sum(r['slots'] for r in running.values() if r['k'] == k)

    def finish(name, rc, note=''):
        r = running.pop(name)
        s = dict(r['status'], rc=rc, end=time.strftime('%F %T'), wall_s=round(time.time() - r['t0'], 1), note=note,
                 nes_rss_gb_after=round(rss_kb(r['nes_pid']) / 1048576, 2))
        with open(os.path.join(jdir, name, 'status.json'), 'w') as f:
            json.dump(s, f, indent=1)
        farm.log('job %s on i%d finished rc=%s wall=%ds %s' % (name, r['k'], rc, s['wall_s'], note))
        return rc

    farm.log('runner pid %d: %d jobs (%d already done) on instances %s, max %d slots each' % (os.getpid(), len(pending), skipped, insts, maxper))
    failures, last_cap_msg = 0, ''
    try:
        while (pending or running) and not stopping['flag']:
            for name in list(running):
                r = running[name]; rc = r['proc'].poll()
                if rc is not None:
                    failures += finish(name, rc) != 0
                elif r['timeout'] and time.time() - r['t0'] > r['timeout']:
                    os.killpg(r['proc'].pid, signal.SIGTERM); r['proc'].wait(30)
                    failures += 1; finish(name, -1, 'timeout')
            write_running()
            if pending:
                ok, msg, _ = cap_check(cfg, window=0.5)
                if not ok:
                    if msg != last_cap_msg:
                        farm.log('not starting new jobs: ' + msg)
                    last_cap_msg = msg; time.sleep(10); continue
                last_cap_msg = ''
                st = farm.load()
                j = pending[0]
                order = sorted((k for k in insts if slots_on(k) + j['slots'] <= maxper), key=lambda k: (slots_on(k), dispatched[k], k))
                chosen = None
                for k in order:
                    inst = st['instances'][k]
                    alive = verify_own(cfg, farm, inst, 'nes', True) and verify_own(cfg, farm, inst, 'api', True)
                    big = alive and rss_kb(inst['nes_pid']) > cfg['rss_restart_gb'] * 1048576
                    if (not alive or big) and slots_on(k) == 0:
                        if restart_instance(cfg, farm, k, 'NES not running' if not alive else 'NES RSS %.1f GB > %s GB, idle' % (rss_kb(inst['nes_pid']) / 1048576, cfg['rss_restart_gb'])):
                            st = farm.load(); inst = st['instances'][k]; alive, big = True, False
                    if alive and not big and health(inst['api_port'], 5)[0]:
                        chosen = inst; break
                if chosen is not None:
                    pending.pop(0)
                    c = ctx(j, chosen)
                    os.makedirs(c['job_dir'], exist_ok=True)
                    cmd = j['cmd']
                    if isinstance(cmd, str):
                        cmd = _fmt(cmd, c)
                        argv = ['/bin/bash', '-c', cmd] if j.get('shell') else shlex.split(cmd)
                    else:
                        argv = [_fmt(x, c) for x in cmd]
                    env = dict(os.environ, **cfg['default_job_env'])
                    env.update({k2: _fmt(str(v), c) for k2, v in j['env'].items()})
                    env.update(NESFARM_HOST='127.0.0.1', NESFARM_PORT=str(chosen['api_port']), NESFARM_TAG=a.tag,
                               NESFARM_INSTANCE=str(chosen['k']), NESFARM_JOB=j['name'])
                    cwd = _fmt(j.get('cwd', c['job_dir']), c)
                    lf = open(os.path.join(c['job_dir'], 'job.log'), 'w')
                    p = subprocess.Popen(argv, cwd=cwd, env=env, stdout=lf, stderr=subprocess.STDOUT,
                                         stdin=subprocess.PIPE if j.get('stdin') is not None else subprocess.DEVNULL,
                                         start_new_session=True)
                    if j.get('stdin') is not None:
                        p.stdin.write(j['stdin'].encode()); p.stdin.close()
                    lf.close()
                    status = dict(name=j['name'], instance=chosen['k'], port=chosen['api_port'], pid=p.pid, argv=argv, cwd=cwd,
                                  start=time.strftime('%F %T'), nes_rss_gb_before=round(rss_kb(chosen['nes_pid']) / 1048576, 2))
                    with open(os.path.join(c['job_dir'], 'status.json'), 'w') as f:
                        json.dump(status, f, indent=1)
                    dispatched[chosen['k']] += 1
                    running[j['name']] = dict(proc=p, k=chosen['k'], slots=j['slots'], t0=time.time(), status=status,
                                              nes_pid=chosen['nes_pid'], timeout=j.get('timeout_s'))
                    farm.log('job %s -> i%d (port %d) pid %d [%d/%d slots]' % (j['name'], chosen['k'], chosen['api_port'], p.pid, slots_on(chosen['k']), maxper))
                    write_running()
                    time.sleep(cfg['job_stagger_s'])
                    continue
            time.sleep(2)
        if stopping['flag']:
            farm.log('runner stopping: terminating %d running jobs' % len(running))
            for name, r in list(running.items()):
                with contextlib.suppress(ProcessLookupError):
                    os.killpg(r['proc'].pid, signal.SIGTERM)
                with contextlib.suppress(subprocess.TimeoutExpired):
                    r['proc'].wait(30)
                failures += 1; finish(name, -15, 'interrupted')
    finally:
        with open(os.path.join(farm.dir, 'running.json'), 'w') as f:
            json.dump({}, f)
        with contextlib.suppress(OSError):
            os.remove(lockp)
    farm.log('runner done: %d pending left, %d failed' % (len(pending), failures))
    sys.exit(1 if failures or pending else 0)


def cmd_guard(cfg, a):
    stop = os.path.join(cfg['farm_root'], 'STOP_NEW')
    os.makedirs(cfg['farm_root'], exist_ok=True)
    glog = os.path.join(cfg['farm_root'], 'guard.log')

    def log(m):
        line = '%s %s' % (time.strftime('%F %T'), m)
        print(line, flush=True)
        with open(glog, 'a') as f:
            f.write(line + '\n')
    log('guard start: caps %s cores, %s GB RAM, RSS restart %s GB%s' % (cfg['max_cores'], cfg['max_ram_gb'], cfg['rss_restart_gb'], ' [dry-run]' if a.dry_run else ''))
    while True:
        tot, used = machine_mem()
        pids = all_farm_pids(cfg)
        cores = cpu_cores(pids, 2.0) if pids else 0.0
        over = []
        if used > cfg['max_ram_gb']:
            over.append('used RAM %.0f GB > %s' % (used, cfg['max_ram_gb']))
        if cores > cfg['max_cores']:
            over.append('nesfarm cores %.1f > %s' % (cores, cfg['max_cores']))
        if over and not a.dry_run:
            with open(stop, 'w') as f:
                f.write('guard %s: %s\n' % (time.strftime('%F %T'), '; '.join(over)))
        elif not over and os.path.exists(stop) and open(stop).read().startswith('guard') and not a.dry_run:
            os.remove(stop); log('caps back under limits: STOP_NEW removed')
        parts = []
        for t in ([a.tag] if a.tag else all_tags(cfg)):
            farm = Farm(cfg, t, a.dry_run)
            try:
                st = farm.load()
            except (OSError, ValueError):
                continue
            running, managed = farm.running_jobs(), farm.runner_pid() is not None
            for inst in st['instances']:
                if not verify_own(cfg, farm, inst, 'nes', True):
                    continue
                r = rss_kb(inst['nes_pid']) / 1048576
                parts.append('%s/i%d:%.1fGB' % (t, inst['k'], r))
                if r > cfg['rss_restart_gb']:
                    # Idle = a runner owns the tag and reports no job on this instance. Without a runner we cannot
                    # know whether someone is using the instance by hand (an idle NES still burns 1-2 cores),
                    # so we only restart then with --restart-unmanaged.
                    busy_jobs = len(running.get(inst['k'], []))
                    if (managed and busy_jobs == 0) or (not managed and a.restart_unmanaged):
                        log('%s/i%d RSS %.1f GB > %s and idle (%s): restart' % (t, inst['k'], r, cfg['rss_restart_gb'],
                            'runner reports 0 jobs' if managed else 'no runner, --restart-unmanaged'))
                        restart_instance(cfg, farm, inst['k'], 'guard: RSS %.1f GB' % r)
                    else:
                        log('%s/i%d RSS %.1f GB > %s: not restarting (%s)' % (t, inst['k'], r, cfg['rss_restart_gb'],
                            '%d jobs running' % busy_jobs if managed else 'no runner on this tag; use --restart-unmanaged'))
        log('load %.1f, used RAM %.0f/%.0f GB, nesfarm cores %.1f%s | %s' % (loadavg(), used, tot, cores,
            (' OVER: ' + '; '.join(over)) if over else '', ' '.join(parts)))
        if a.once:
            return
        time.sleep(a.interval)


def main(argv=None):
    ap = argparse.ArgumentParser(prog='nesfarm', description=__doc__.split('\n')[0])
    ap.add_argument('--config', help='JSON config (default: $NESFARM_CONFIG, ./nesfarm.json, ~/.config/nesfarm.json, <pkg>/nesfarm.json)')
    ap.add_argument('--dry-run', action='store_true', help='print what would happen; start or stop nothing')
    common = argparse.ArgumentParser(add_help=False)   # same options accepted after the subcommand
    common.add_argument('--config', default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    common.add_argument('--dry-run', action='store_true', default=argparse.SUPPRESS, help='print what would happen; start or stop nothing')
    sp = ap.add_subparsers(dest='cmd', required=True)
    _add = sp.add_parser
    sp.add_parser = lambda *x, **kw: _add(*x, parents=[common], **kw)
    p = sp.add_parser('up', help='create and start N instances for a tag')
    p.add_argument('--build', required=True, help='NES build dir (with Binaries/BrainGenix-NES) or the Binaries dir')
    p.add_argument('--n', type=int, required=True)
    p.add_argument('--base-port', type=int, required=True, help='instance k uses base+stride*k .. +4 (API, callback, NES, EVM, neuroglancer)')
    p.add_argument('--tag', required=True)
    p.add_argument('--link-model', action='append', help='saved model dir to symlink into each instance (repeatable)')
    p = sp.add_parser('status', help='instances, RSS, threads, cores, jobs, health')
    p.add_argument('--tag')
    p = sp.add_parser('run', help='dispatch jobs from a job file to the instances of a tag')
    p.add_argument('--tag', required=True); p.add_argument('--job-file', required=True)
    p.add_argument('--max-per-instance', type=int); p.add_argument('--instances', type=lambda s: [int(x) for x in s.split(',')])
    p.add_argument('--rerun', action='store_true', help='also run jobs whose last run ended rc=0')
    p.add_argument('--detach', action='store_true', help='run the queue in the background (log: <tag>/run.log)')
    p = sp.add_parser('guard', help='monitor caps and RSS; set STOP_NEW; restart idle instances above the RSS cap')
    p.add_argument('--tag', help='only this tag (default: all)'); p.add_argument('--interval', type=int, default=60)
    p.add_argument('--once', action='store_true')
    p.add_argument('--restart-unmanaged', action='store_true', help='also restart instances above the RSS cap when no runner owns the tag')
    p = sp.add_parser('down', help="stop this tag's instances (only processes recorded in its state)")
    p.add_argument('--tag', required=True); p.add_argument('--k', type=int); p.add_argument('--force', action='store_true')
    p = sp.add_parser('restart', help='restart one instance of a tag')
    p.add_argument('--tag', required=True); p.add_argument('--k', type=int, required=True); p.add_argument('--force', action='store_true')
    p = sp.add_parser('clean', help='delete leftover resident sims through the API (or --restart)')
    p.add_argument('--tag', required=True); p.add_argument('--k', type=int)
    p.add_argument('--max-id', type=int, default=200, help='try sim IDs 0..max-id (NES has no list route)')
    p.add_argument('--ids', help='comma-separated sim IDs instead of 0..max-id')
    p.add_argument('--timeout', type=float, default=20); p.add_argument('--restart', action='store_true')
    p.add_argument('--force', action='store_true')
    a = ap.parse_args(argv)
    cfg = load_config(a.config)
    {'up': cmd_up, 'status': cmd_status, 'run': cmd_run, 'guard': cmd_guard, 'down': cmd_down,
     'restart': cmd_restart, 'clean': cmd_clean}[a.cmd](cfg, a)


if __name__ == '__main__':
    main()
