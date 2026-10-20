# Qoder Usage Statusbar (English)

A **local, offline** credit/context status bar for [Qoder](https://qoder.com) / QoderWork.
It shows the current model's **credit consumption**, **context-window occupancy**, and
**per-turn duration** — all parsed from your machine's Qoder session logs. No network,
nothing uploaded.

Inspired by [zcode-token-usage-statusbar](https://github.com/Clannadad/zcode-token-usage-statusbar),
but scoped to what Qoder actually exposes locally.

## Why it differs from the zcode version

The zcode tool shows real token counts, tok/s, and vendor **remaining quota + reset
countdown** by reading a local SQLite (real tokens) plus calling vendor quota APIs.

Neither premise holds for Qoder:

- Qoder zeroes out `input_tokens / output_tokens / cache_*` in its on-disk logs, so real
  token counts and tok/s are **not derivable**.
- Local files only store the plan name (Free/paid), **not a remaining-credit number**, and
  there is no public quota API. Balance is only visible on the Qoder web dashboard.

What *is* reliable and fully local: `usage.credits` (per-request credit burn) and
`context_usage_ratio`. So this project leads with those plus per-turn duration, and leaves
"balance / reset" as an optional future module (would require fragile web scraping with
ToS risk).

## Metrics

| Metric | Meaning | Source |
|---|---|---|
| context now / peak | current / peak context-window occupancy for the session (icon colour green→red) | `usage.context_usage_ratio` |
| session cr | cumulative credits consumed in the current session | sum of `usage.credits` |
| today cr | cumulative credits consumed today (local timezone) | same |
| today reqs | request count today | log count |
| avg turn | mean wall-clock gap between turns (rough per-turn duration) | timestamp diffs |
| model | current model id | `message.model` |

## Install

```bash
pip install -e .            # engine (--once / --watch need no extra deps)
pip install -e ".[tray]"    # + pystray and Pillow for the tray (--tray)
```

## Usage

```bash
qoder-usage                 # print a one-shot summary
qoder-usage --watch         # live terminal refresh every 15s (Ctrl+C to quit)
qoder-usage --tray          # system-tray icon, hover for details
```

## Data sources

Scanned automatically (priority order): `~/.qoderworkcn/projects/**/*.jsonl` (QoderWork)
and `~/.qoder/projects/**/*.jsonl` (Qoder IDE). Read-only.

## License

MIT
