---
name: cluster-21
description: "Skill for the Cluster_21 area of teams-translator. 4 symbols across 1 files."
---

# Cluster_21

4 symbols | 1 files | Cohesion: 50%

## When to Use

- Working with code in `src/`
- Understanding how _set_caption_visible, _setup_tray, _make_icon_fallback work
- Modifying cluster_21-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `src/app_controller.py` | _set_caption_visible, _setup_tray, _make_icon_fallback, _set_mode |

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `_set_caption_visible` | Function | `src/app_controller.py` | 116 |
| `_setup_tray` | Function | `src/app_controller.py` | 146 |
| `_make_icon_fallback` | Function | `src/app_controller.py` | 257 |
| `_set_mode` | Function | `src/app_controller.py` | 320 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `_set_mode → _notify` | cross_community | 4 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Cluster_23 | 2 calls |
| _stop_ | 1 calls |
| Ui | 1 calls |
| _start_ | 1 calls |

## How to Explore

1. `gitnexus_context({name: "_set_caption_visible"})` — see callers and callees
2. `gitnexus_query({query: "cluster_21"})` — find related execution flows
3. Read key files listed above for implementation details
