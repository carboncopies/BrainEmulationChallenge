#!/usr/bin/env python3
"""Offline tests for nesfarm: no NES is started. Uses a temporary farm root, a fake build and fake state.
Run: python3 -m unittest discover -s tests -v   (from the multi_instance folder)"""
import json, os, re, socket, subprocess, sys, tempfile, time, unittest

PKG = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PKG)
import nesfarm  # noqa: E402

PROTECTED = [3156209, 1972355]


def free_base():
    """A base port with 40 free ports above it (test ports only, never bound by the tests except where stated)."""
    for base in range(19400, 29000, 50):
        if all(nesfarm.port_free(p) for p in range(base, base + 40)):
            return base
    raise RuntimeError('no free test ports')


class T(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = self.tmp.name
        self.build = os.path.join(t, 'build')
        os.makedirs(os.path.join(self.build, 'Binaries'))
        for f in ('BrainGenix-NES', 'NES.yaml'):
            open(os.path.join(self.build, 'Binaries', f), 'w').write('Network_NES_API_Port: 8002\nOutput_BasePath: /x\n')
        open(os.path.join(t, 'api'), 'w').write('')
        open(os.path.join(t, 'users.json'), 'w').write('{}')
        self.cfgp = os.path.join(t, 'cfg.json')
        json.dump({'farm_root': os.path.join(t, 'farm'), 'api_binary': os.path.join(t, 'api'),
                   'users_json': os.path.join(t, 'users.json'), 'protected_pids': PROTECTED, 'max_ram_gb': 100000,
                   'max_cores': 100000}, open(self.cfgp, 'w'))
        self.base = free_base()

    def tearDown(self):
        self.tmp.cleanup()

    def cli(self, *args):
        return subprocess.run([sys.executable, os.path.join(PKG, 'nesfarm.py'), '--config', self.cfgp] + list(args),
                              capture_output=True, text=True, timeout=120)

    def cfg(self):
        return nesfarm.load_config(self.cfgp)

    def fake_state(self, tag, n, base, pids=None):
        cfg = self.cfg(); f = nesfarm.Farm(cfg, tag)
        os.makedirs(f.dir, exist_ok=True)
        st = {'tag': tag, 'build': self.build, 'base_port': base, 'instances': []}
        for k in range(n):
            d = os.path.join(f.dir, 'i%d' % k)
            os.makedirs(os.path.join(d, 'nes'), exist_ok=True); os.makedirs(os.path.join(d, 'api'), exist_ok=True)
            st['instances'].append({'k': k, 'dir': d, 'api_port': base + 10 * k, 'nes_port': base + 10 * k + 2,
                                    'nes_pid': (pids or {}).get(k), 'nes_starttime': None, 'api_pid': None})
        f.save(st)
        return f, st

    # ---- tests

    def test_up_dry_run_plans_and_creates_nothing(self):
        r = self.cli('up', '--build', self.build, '--n', '3', '--base-port', str(self.base), '--tag', 'exp1', '--dry-run')
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertIn('[dry-run] i2: API %d' % (self.base + 20), r.stdout)
        self.assertIn('NES %d' % (self.base + 22), r.stdout)
        self.assertFalse(os.path.exists(os.path.join(self.tmp.name, 'farm', 'exp1', 'state.json')))

    def test_port_in_use_refused(self):
        s = socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('127.0.0.1', self.base + 12)); s.listen(1)
        try:
            r = self.cli('up', '--build', self.build, '--n', '2', '--base-port', str(self.base), '--tag', 'exp1', '--dry-run')
        finally:
            s.close()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('%d (in use)' % (self.base + 12), r.stderr)

    def test_tags_do_not_share_ports(self):
        me = os.getpid()  # a live pid makes the fake tag count as "running" for the reservation check
        f, st = self.fake_state('math', 2, self.base)
        st['instances'][0]['api_pid'] = me; f.save(st)
        r = self.cli('up', '--build', self.build, '--n', '2', '--base-port', str(self.base + 10), '--tag', 'std', '--dry-run')
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('(tag math)', r.stderr)
        r = self.cli('up', '--build', self.build, '--n', '2', '--base-port', str(self.base + 20), '--tag', 'std', '--dry-run')
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_bad_tag_and_missing_build(self):
        self.assertNotEqual(self.cli('up', '--build', self.build, '--n', '1', '--base-port', str(self.base), '--tag', '../x', '--dry-run').returncode, 0)
        self.assertNotEqual(self.cli('up', '--build', '/nonexistent', '--n', '1', '--base-port', str(self.base), '--tag', 'x', '--dry-run').returncode, 0)

    def test_caps_refuse_up(self):
        c = json.load(open(self.cfgp)); c['max_ram_gb'] = 0.001; json.dump(c, open(self.cfgp, 'w'))
        r = self.cli('up', '--build', self.build, '--n', '1', '--base-port', str(self.base), '--tag', 'x', '--dry-run')
        self.assertNotEqual(r.returncode, 0); self.assertIn('refusing to start', r.stderr)

    def test_run_dry_run_dispatch_and_placeholders(self):
        self.fake_state('exp1', 2, self.base)
        jobs = {'defaults': {'env': {'A': '1'}},
                'jobs': [{'name': 'b%d' % i, 'cmd': 'echo {host}:{port} {nes_port} i{instance} {tag} {name}'} for i in range(5)]
                + [{'name': 'big', 'cmd': ['run.py', '-Port', '{port}'], 'slots': 3}]}
        jf = os.path.join(self.tmp.name, 'jobs.json'); json.dump(jobs, open(jf, 'w'))
        r = self.cli('run', '--tag', 'exp1', '--job-file', jf, '--dry-run')
        self.assertEqual(r.returncode, 0, r.stderr)
        lines = [l for l in r.stdout.splitlines() if re.match(r'\[dry-run\] b\d ', l)]
        self.assertEqual(len(lines), 5)
        self.assertIn('b0 -> i0', lines[0]); self.assertIn('b1 -> i1', lines[1]); self.assertIn('b2 -> i0', lines[2])
        self.assertIn('127.0.0.1:%d %d i0 exp1 b0' % (self.base, self.base + 2), lines[0])
        big = [l for l in r.stdout.splitlines() if l.startswith('[dry-run] big')][0]
        self.assertIn('3 slots', big); self.assertRegex(big, r'big -> i1 .*run\.py -Port %d$' % (self.base + 10,))

    def test_job_needing_too_many_slots_refused(self):
        self.fake_state('exp1', 1, self.base)
        jf = os.path.join(self.tmp.name, 'j.json'); json.dump({'jobs': [{'name': 'x', 'cmd': 'true', 'slots': 4}]}, open(jf, 'w'))
        r = self.cli('run', '--tag', 'exp1', '--job-file', jf, '--dry-run')
        self.assertNotEqual(r.returncode, 0)

    def test_down_refuses_protected_and_foreign_pids(self):
        # protected pid recorded in state: refused (and never signalled)
        f, st = self.fake_state('exp1', 3, self.base, pids={0: PROTECTED[0]})
        # foreign pid: our own test process, recorded with a wrong start time and wrong cwd
        st['instances'][1]['nes_pid'] = os.getpid(); st['instances'][1]['nes_starttime'] = 1
        # pid 1 (init): not ours either
        st['instances'][2]['nes_pid'] = 1; st['instances'][2]['nes_starttime'] = nesfarm.proc_stat(1)['starttime']
        f.save(st)
        r = self.cli('down', '--tag', 'exp1')
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('REFUSED to stop protected pid %d' % PROTECTED[0], r.stdout)
        self.assertIn('REFUSED to stop pid %d' % os.getpid(), r.stdout)
        self.assertIn('REFUSED to stop pid 1', r.stdout)
        self.assertTrue(nesfarm.pid_alive(os.getpid()) and nesfarm.pid_alive(1))

    def test_down_stops_own_verified_process(self):
        f, st = self.fake_state('exp1', 1, self.base)
        d = st['instances'][0]['dir']
        pid, stt = nesfarm.spawn(['sleep', '300'], os.path.join(d, 'nes'), os.path.join(d, 'nes.log'))
        st['instances'][0]['nes_pid'], st['instances'][0]['nes_starttime'] = pid, stt; f.save(st)
        r = self.cli('down', '--tag', 'exp1', '--dry-run')
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr); self.assertIn('would stop i0 nes pid %d' % pid, r.stdout)
        self.assertTrue(nesfarm.pid_alive(pid))
        r = self.cli('down', '--tag', 'exp1')
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        time.sleep(0.5)
        try:
            os.waitpid(pid, os.WNOHANG)   # reap the zombie (it is our child)
        except ChildProcessError:
            pass
        self.assertFalse(nesfarm.pid_alive(pid))
        self.assertIsNone(json.load(open(f.state_path))['instances'][0]['nes_pid'])

    def test_config_env_expansion(self):
        os.environ['NESFARM_TEST_X'] = '/opt/x'
        try:
            c = json.load(open(self.cfgp)); c['api_binary'] = '${NESFARM_TEST_X:-/y}/api'; json.dump(c, open(self.cfgp, 'w'))
            self.assertEqual(self.cfg()['api_binary'], '/opt/x/api')
        finally:
            del os.environ['NESFARM_TEST_X']
        self.assertEqual(self.cfg()['api_binary'], '/y/api')
        self.assertIn(3156209, self.cfg()['protected_pids'])

    def test_nes_yaml_rewrite(self):
        src = os.path.join(self.tmp.name, 'in.yaml'); dst = os.path.join(self.tmp.name, 'out.yaml')
        open(src, 'w').write('Network_NES_API_Port: 8002\nOther: 1\nOutput_BasePath: /old\n')
        nesfarm.write_nes_yaml(src, dst, 9002, '/new/out', {'VSDA_EM_MaxVoxelArraySize': 5000})
        t = open(dst).read()
        self.assertIn('Network_NES_API_Port: 9002', t); self.assertIn('Output_BasePath: /new/out', t)
        self.assertIn('Other: 1', t); self.assertIn('VSDA_EM_MaxVoxelArraySize: 5000', t); self.assertNotIn('8002', t)


if __name__ == '__main__':
    unittest.main(verbosity=2)
