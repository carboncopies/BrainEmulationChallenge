# nesfarm: several NES stacks side by side, one queue per experiment

`nesfarm` starts N private NES+API pairs from a chosen NES build, feeds them jobs (growth batches or simulation scripts), restarts instances whose memory has grown, and stops only what it started. Each experiment gets a **tag** with its own ports, folders, state and logs, so two experiments (say `std` and `math`) can run at the same time without touching each other or the main NES.

It uses Python 3 standard library only. There is one file, `nesfarm.py`, plus the `nesfarm` wrapper.

## Quick start
```
cp nesfarm.example.json ~/.config/nesfarm.json        # once per machine; set api_binary, users_json, farm_root
./nesfarm up --build ~/BrainGenix/wt/nes-linefix --n 6 --base-port 8600 --tag exp1
./nesfarm status                                      # all tags: pids, RSS, threads, cores, jobs, health
./nesfarm run --tag exp1 --job-file jobs.json --dry-run   # show where each job would go
./nesfarm run --tag exp1 --job-file jobs.json --detach    # queue in the background (log: <farm_root>/exp1/run.log)
./nesfarm guard --interval 60 &                       # caps + RSS watchdog for all tags (optional; log: <farm_root>/guard.log)
./nesfarm clean --tag exp1                            # delete leftover resident sims (or: clean --tag exp1 --restart)
./nesfarm down --tag exp1                             # stop exp1's instances only
```
Instance k of a tag uses ports `base + 10k` (API), `+1` (RPC callback), `+2` (NES), `+3` (EVM) and `+4` (Neuroglancer). Scripts connect to the API port, which `{port}` gives in job files.

## Commands
| command | what it does |
|---|---|
| `up --build DIR --n N --base-port P --tag T [--link-model DIR ...]` | Makes `<farm_root>/T/i<k>/{nes,api,out}`: the binaries are symlinked from `DIR/Binaries`, with its own `NES.yaml` (port, Output_BasePath), `API.cfg`, `Source/Core/Config/users.json` and optional symlinked saved models. It starts NES, waits for its port, starts the API, and waits for `/Hello` and `/Diagnostic/Version`. Before starting, it refuses if any port is in use or reserved by another tag, or if the caps would be exceeded. If one instance fails, it stops what it started. |
| `status [--tag T]` | Machine load and RAM, then per instance: verified pids, NES RSS, thread count, cores used, running jobs, health. |
| `run --tag T --job-file F [--detach] [--rerun] [--max-per-instance M] [--instances 0,2]` | A queue. Each job goes to the healthy instance with the fewest busy slots; ties go to the instance with fewer jobs so far. An instance holds at most 3 slots (configurable). Before dispatch it checks the caps and `STOP_NEW`. It restarts an instance whose NES RSS exceeds 10 GB **only when no job is running on it**; a busy instance waits. Jobs that finished with rc 0 are skipped on rerun. On Ctrl-C or SIGTERM it terminates its own job process groups. One runner per tag. |
| `guard [--tag T] [--interval 60] [--once] [--restart-unmanaged]` | Every interval it logs load, machine RAM, nesfarm cores and per-instance RSS. It writes `<farm_root>/STOP_NEW` when the caps are exceeded and removes it when back under; runners of every tag then hold new jobs. It restarts an instance above the RSS cap when that tag's runner reports no job on it. With no runner on the tag it only restarts with `--restart-unmanaged`, because it cannot tell whether someone is using the instance by hand. |
| `restart --tag T --k K [--force]` | Restart one instance (refused while a runner has jobs on it unless `--force`). |
| `clean --tag T [--max-id 200 \| --ids 3,7] [--restart]` | Logs in and calls `Simulation/DeleteResidentByID` for sim IDs 0..max-id. NES has no "list sims" route; IDs count up from 0 per NES process. `--restart` restarts the instances instead, which drops every sim **and** the leaked RSS. Refused while a runner is active unless `--force`. |
| `down --tag T [--k K] [--force]` | Stops this tag's API then NES processes (SIGTERM, then SIGKILL after 30 s). Refused while a runner is active unless `--force`. |
| global `--dry-run`, `--config FILE` | Also accepted after the subcommand. `--dry-run` starts and stops nothing and prints the plan. |

## Config
Search order: `--config`, `$NESFARM_CONFIG`, `./nesfarm.json`, `~/.config/nesfarm.json`, `<package>/nesfarm.json`. Values may use `${VAR:-default}`. Keys (defaults in `nesfarm.py`; full example in `nesfarm.example.json`):

| key | default | meaning |
|---|---|---|
| `farm_root` | `~/.local/state/nesfarm` | per-tag state, instance folders, logs |
| `api_binary`, `users_json` | env `NESFARM_API_BINARY`, `NESFARM_USERS_JSON` | the BrainGenix-API executable and its users.json (required) |
| `nes_venv` | empty | venv put on PATH for NES (the old `inst.sh` sourced the NES venv) |
| `api_user`, `api_password` | the BEC scripts' local dev login | used by `clean` |
| `max_cores` | 48 | cores used by all nesfarm processes of all tags (NES, API, runners, jobs), measured from /proc |
| `max_ram_gb` | 250 | machine-wide used RAM (MemTotal − MemAvailable) |
| `rss_restart_gb` | 10 | restart an idle instance above this NES RSS |
| `max_jobs_per_instance` | 3 | slots per instance |
| `est_cores_per_instance`, `est_ram_gb_per_instance` | 2, 3 | what `up` adds per instance when checking caps |
| `protected_pids` | `[3156209, 1972355]` | never signalled, whatever the state file says |
| `port_stride`, `job_stagger_s`, `start_timeout_s` | 10, 5, 90 | |
| `default_job_env` | OMP/OPENBLAS/MKL threads = 1 | added to every job's environment |

`NESFARM_MAX_CORES`, `NESFARM_MAX_RAM_GB`, `NESFARM_RSS_RESTART_GB` and `NESFARM_MAX_JOBS_PER_INSTANCE` override the file.

## Job file
```json
{"defaults": {"slots": 1, "cwd": "{job_dir}", "env": {"A": "1"}, "stdin": null, "timeout_s": null, "shell": false},
 "jobs": [{"name": "j1", "cmd": "python3 my_sim.py --port {port}"},
          {"name": "j2", "cmd": ["python3", "my_sim.py", "--port", "{port}"], "slots": 2}]}
```
- `cmd` is a string (split like a shell line, no shell unless `"shell": true`) or a list.
- Placeholders: `{host}`, `{port}` (API), `{nes_port}`, `{instance}`, `{tag}`, `{name}`, `{job_dir}`, `{farm_dir}`, `{out_dir}`. After that, `$ENV_VARS` are expanded. Write `{{ }}` for literal braces.
- Jobs also get `NESFARM_HOST`, `NESFARM_PORT`, `NESFARM_TAG`, `NESFARM_INSTANCE` and `NESFARM_JOB` in their environment.
- Each job writes `<farm_root>/<tag>/jobs/<name>/{job.log,status.json}`. `status.json` holds the instance, port, pid, argv, start, end, rc and NES RSS before and after.
- `slots`: a job that runs k growths or sims at once on its instance should take k slots.

**Example: gen_autonm_labels.py batches** (`examples/jobs_gen_autonm.json`). One job per seed, because the stock generator puts one `-randomseed` on every row. Each job takes `"slots": 3` with `-batchlimit 3 -deleteresident`, and `"stdin": "n\n"` answers its final "compare?" prompt. Never use `-fitcpus`: it sizes batches to the client's `os.cpu_count()` (64 here), and 6 concurrent growths have crashed a NES.

**Example: simulation scripts** (`examples/jobs_sim_script.json`). One slot each, so up to 3 per instance. The script must take the port and delete its sims in `finally`. If it loads saved models, start the tag with `up --link-model <saved model dir>`.

## Lessons built in (from earlier runs)
- **NES leaks about 0.2–0.3 GB RSS per simulation**, even after `DeleteResidentByID`. Restart above about 10 GB, but only when idle; `run` and `guard` do this. Still delete sims and residents after every use (`-deleteresident`, script `finally`), and use `clean` for leftovers.
- **Threads and load average:** one NES has about 500–560 threads (499 at idle on nes-linefix). The load average counts runnable threads, so it can read 200+ while the cores are not saturated. The caps therefore use measured CPU time of nesfarm's own processes plus machine-wide RAM, not the load average. An idle NES still burns about 1–2 cores, so stop tags you no longer use.
- **At most 3 concurrent growths or sims per NES.** 6 crashed a NES before.
- **API needs `../Source/Core/Config/users.json` relative to its working directory**, or clients get "Service unavailable". `up` puts a copy there.
- **Client checksum:** the PythonClient hashes its known route list and compares it with `/Diagnostic/Version` (`APIChecksum`). If an NES build adds routes (e.g. a locally patched option), stock clients refuse to connect ("API Checksum Mismatch"). Use the client that matches the build (put it first on PYTHONPATH in the job `env`), or add the routes to `_KNOWN_ROUTES` in that client copy.
- **One seed per gen_autonm batch** (see above). Use a sheet copy with a `randomseed` column, or one job per seed.
- **Kill by verified PID, never with `pkill -f`.** A pattern that matches your own shell's command line kills your shell.
- `setsid nohup … & echo $!` records the wrapper, not NES. nesfarm starts the binaries directly in a new session and records the real pid and its start time.

## Safety rules (what it will not do)
- It never signals a pid unless all of these hold: the pid is in this tag's `state.json`; it is alive; its kernel start time equals the recorded one (no pid reuse); its working directory is the recorded instance folder inside this tag's folder; and it is not in `protected_pids` (the main NES 3156209 and API 1972355 by default). Anything else is logged as REFUSED.
- It does not touch other tags' instances, other experiments' NES stacks (anything it did not start), the main NES, git, email or Drive.
- It does not pick ports for you or move a tag to free ports. It refuses ports in use or reserved by another tag.
- It does not restart an instance that has running jobs. `guard` does not restart an instance with no runner unless told to.
- It does not build NES, edit model files or delete output folders. It only removes resident sims, through the API.
- It does not share a queue across tags. Each tag has one runner and its own instances.

## Tests
- `python3 -m unittest discover -s tests -v`: 11 offline tests (no NES). They cover the dry-run plans for `up` and `run`, port-in-use refusal, tag port isolation, cap refusal, slot limits, refusal to stop protected, foreign or reused pids, stopping a verified own process, config expansion and the NES.yaml rewrite.
- `NESFARM_TEST_BUILD=<NES build> tests/real_test.sh [base_port=8900] [cpus=60-63]`: 2 real instances pinned to 4 CPUs. It runs 4 jobs that create and delete a tiny sim, then guard, clean and down. It checks that no process is left in the test farm, the ports are free, the protected pids have the same start time, and the machine's set of NES and API pids is unchanged.
