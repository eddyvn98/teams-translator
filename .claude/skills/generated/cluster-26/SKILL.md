---
name: cluster-26
description: "Skill for the Cluster_26 area of teams-translator. 8 symbols across 1 files."
---

# Cluster_26

8 symbols | 1 files | Cohesion: 78%

## When to Use

- Working with code in `src/`
- Understanding how _on_loopback_result, _stabilize_loopback_text, _on_stt_result work
- Modifying cluster_26-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `src/app_controller.py` | _on_loopback_result, _stabilize_loopback_text, _on_stt_result, _on_teams_caption, _append_session_text (+3) |

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `_on_loopback_result` | Function | `src/app_controller.py` | 432 |
| `_stabilize_loopback_text` | Function | `src/app_controller.py` | 459 |
| `_on_stt_result` | Function | `src/app_controller.py` | 478 |
| `_on_teams_caption` | Function | `src/app_controller.py` | 491 |
| `_append_session_text` | Function | `src/app_controller.py` | 504 |
| `_maybe_update_summary` | Function | `src/app_controller.py` | 526 |
| `_kick_summary_worker` | Function | `src/app_controller.py` | 529 |
| `_toggle_summary_updates` | Function | `src/app_controller.py` | 758 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `_on_loopback_result → Start` | cross_community | 4 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Ui | 2 calls |
| Cluster_9 | 1 calls |
| Cluster_23 | 1 calls |

## How to Explore

1. `gitnexus_context({name: "_on_loopback_result"})` — see callers and callees
2. `gitnexus_query({query: "cluster_26"})` — find related execution flows
3. Read key files listed above for implementation details
