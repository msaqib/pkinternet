# Exp 03 — Running a long experiment on a server (setup)

For a 24h+ run you want a machine that stays on and a session that survives SSH
disconnects. The measurements run on **RIPE Atlas** (not on this server) — the
server only schedules them and pulls/auto-pushes the results. So any always-on
Linux box works.

## 0. Prerequisites
- Python 3, and the deps: `requests`, `dnspython`, `python-dotenv`
- Your `RIPE_API_KEY`
- `tmux` (so the run survives disconnects) — `which tmux` to check

## 1. Get the code + deps
```bash
cd ~
git clone https://github.com/msaqib/pkinternet.git      # or: cd pkinternet && git pull
cd pkinternet
python3 -m pip install --user requests dnspython python-dotenv
```

## 2. Configure
```bash
# RIPE key (paste your value; don't commit this file - .env is gitignored)
nano .env                       # add:  RIPE_API_KEY=xxxxxxxx

# git identity, so the auto-commit can succeed
git config user.email "you@example.com"
git config user.name  "Your Name"
```
Edit the top of `experiments/03_longitudinal_routing/trace_monitor.py`:
`RUN_NAME`, `PROBES`, `TARGETS`, `DURATION_HOURS`, `PING_INTERVAL_SEC`, `AUTO_PUSH`.

## 3. Sanity-check cost/volume BEFORE spending credits
```bash
python3 experiments/03_longitudinal_routing/trace_monitor.py stats
```
Shows expected rounds, probe wire traffic, storage footprint, and RIPE credits.
Make sure the credit estimate fits your balance. (1/min ping is the expensive part;
`PING_INTERVAL_SEC=300` or `PING_COMPANION=False` cut it a lot.)

## 4. Run it in tmux (survives laptop close + SSH drops)
```bash
tmux new -s trace
python3 experiments/03_longitudinal_routing/trace_monitor.py schedule   # asks y/N
python3 experiments/03_longitudinal_routing/trace_monitor.py watch       # runs to the end, then auto-pushes
#   detach:  Ctrl-b  then  d        reattach later:  tmux attach -t trace
```
Close your laptop. When the window ends, `watch` writes the final snapshot and
(if `AUTO_PUSH`) commits + pushes the results folder.

## 5. Make auto-push actually work (push rights on the server)
`git clone https://…` is read-only, so the final push fails (gracefully — files
stay saved locally + on RIPE). To enable push, use an SSH deploy key:
```bash
ssh-keygen -t ed25519 -C "server"          # enter through the prompts
cat ~/.ssh/id_ed25519.pub                  # add this at github.com/settings/keys
git remote set-url origin git@github.com:msaqib/pkinternet.git
git push                                   # verify
```
If you skip this, just `fetch` the results to your laptop instead — nothing is lost.

## Getting results without the server
The data lives on RIPE, so you don't strictly need the server running: `schedule`
returns instantly and RIPE runs for the full window on its own. You can then
`fetch` from **any** machine that has `measurements.json` + the API key:
```bash
python3 experiments/03_longitudinal_routing/trace_monitor.py fetch
```

## Commands
| Command | Does |
|---|---|
| `schedule` | Create the RIPE measurements (asks to confirm the credit spend) |
| `stats`    | Estimate/report data volume, storage, credits |
| `fetch`    | One-shot pull → timestamped CSVs/txt |
| `watch`    | Refresh live files each interval, write final snapshot + auto-push at the end |
| `stop`     | Delete the measurements early |
