---
name: start
description: "Skill for the _start_ area of teams-translator. 4 symbols across 1 files."
---

# _start_

4 symbols | 1 files | Cohesion: 50%

## When to Use

- Working with code in `src/`
- Understanding how _start_capture, _start_loopback, _start_stt work
- Modifying _start_-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `src/app_controller.py` | _start_capture, _start_loopback, _start_stt, _start_ocr |

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `_start_capture` | Function | `src/app_controller.py` | 373 |
| `_start_loopback` | Function | `src/app_controller.py` | 386 |
| `_start_stt` | Function | `src/app_controller.py` | 399 |
| `_start_ocr` | Function | `src/app_controller.py` | 412 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `On_toggle → _notify` | cross_community | 5 |
| `_auto_start_capture → _notify` | cross_community | 4 |
| `_set_mode → _notify` | cross_community | 4 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Cluster_23 | 3 calls |

## How to Explore

1. `gitnexus_context({name: "_start_capture"})` — see callers and callees
2. `gitnexus_query({query: "_start_"})` — find related execution flows
3. Read key files listed above for implementation details
