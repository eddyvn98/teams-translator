---
name: stop
description: "Skill for the _stop_ area of teams-translator. 4 symbols across 1 files."
---

# _stop_

4 symbols | 1 files | Cohesion: 67%

## When to Use

- Working with code in `src/`
- Understanding how _stop_current_capture, _stop_loopback, _stop_stt work
- Modifying _stop_-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `src/app_controller.py` | _stop_current_capture, _stop_loopback, _stop_stt, _stop_ocr |

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `_stop_current_capture` | Function | `src/app_controller.py` | 381 |
| `_stop_loopback` | Function | `src/app_controller.py` | 393 |
| `_stop_stt` | Function | `src/app_controller.py` | 406 |
| `_stop_ocr` | Function | `src/app_controller.py` | 424 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `On_toggle → _stop_loopback` | cross_community | 4 |
| `On_toggle → _stop_stt` | cross_community | 4 |
| `On_toggle → _stop_ocr` | cross_community | 4 |

## How to Explore

1. `gitnexus_context({name: "_stop_current_capture"})` — see callers and callees
2. `gitnexus_query({query: "_stop_"})` — find related execution flows
3. Read key files listed above for implementation details
