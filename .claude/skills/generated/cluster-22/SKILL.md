---
name: cluster-22
description: "Skill for the Cluster_22 area of teams-translator. 4 symbols across 1 files."
---

# Cluster_22

4 symbols | 1 files | Cohesion: 50%

## When to Use

- Working with code in `src/`
- Understanding how on_toggle work
- Modifying cluster_22-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `src/app_controller.py` | on_toggle, _toggle_capture, _get_mode_name, _auto_start_capture |

## Entry Points

Start here when exploring this area:

- **`on_toggle`** (Function) — `src/app_controller.py:284`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `on_toggle` | Function | `src/app_controller.py` | 284 |
| `_toggle_capture` | Function | `src/app_controller.py` | 350 |
| `_get_mode_name` | Function | `src/app_controller.py` | 366 |
| `_auto_start_capture` | Function | `src/app_controller.py` | 922 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `On_toggle → _notify` | cross_community | 5 |
| `On_toggle → _stop_loopback` | cross_community | 4 |
| `On_toggle → _stop_stt` | cross_community | 4 |
| `On_toggle → _stop_ocr` | cross_community | 4 |
| `On_toggle → Get` | cross_community | 4 |
| `_auto_start_capture → _notify` | cross_community | 4 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Cluster_23 | 2 calls |
| _start_ | 2 calls |
| _stop_ | 1 calls |
| Ui | 1 calls |

## How to Explore

1. `gitnexus_context({name: "on_toggle"})` — see callers and callees
2. `gitnexus_query({query: "cluster_22"})` — find related execution flows
3. Read key files listed above for implementation details
