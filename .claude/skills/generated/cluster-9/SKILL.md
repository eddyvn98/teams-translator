---
name: cluster-9
description: "Skill for the Cluster_9 area of teams-translator. 6 symbols across 4 files."
---

# Cluster_9

6 symbols | 4 files | Cohesion: 67%

## When to Use

- Working with code in `src/`
- Understanding how start_clipboard_monitor, start_live_caption_monitor, main work
- Modifying cluster_9-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `src/teams_agent.py` | start_clipboard_monitor, start_live_caption_monitor |
| `src/app_controller.py` | TeamsTranslatorApp, start |
| `src/main.py` | main |
| `src/loopback_capture.py` | start_capture |

## Entry Points

Start here when exploring this area:

- **`start_clipboard_monitor`** (Function) — `src/teams_agent.py:155`
- **`start_live_caption_monitor`** (Function) — `src/teams_agent.py:240`
- **`main`** (Function) — `src/main.py:24`
- **`start_capture`** (Function) — `src/loopback_capture.py:145`
- **`start`** (Function) — `src/app_controller.py:909`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `TeamsTranslatorApp` | Class | `src/app_controller.py` | 29 |
| `start_clipboard_monitor` | Function | `src/teams_agent.py` | 155 |
| `start_live_caption_monitor` | Function | `src/teams_agent.py` | 240 |
| `main` | Function | `src/main.py` | 24 |
| `start_capture` | Function | `src/loopback_capture.py` | 145 |
| `start` | Function | `src/app_controller.py` | 909 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `_on_loopback_result → Start` | cross_community | 4 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Ui | 1 calls |

## How to Explore

1. `gitnexus_context({name: "start_clipboard_monitor"})` — see callers and callees
2. `gitnexus_query({query: "cluster_9"})` — find related execution flows
3. Read key files listed above for implementation details
