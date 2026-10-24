---
name: cluster-23
description: "Skill for the Cluster_23 area of teams-translator. 16 symbols across 1 files."
---

# Cluster_23

16 symbols | 1 files | Cohesion: 75%

## When to Use

- Working with code in `src/`
- Understanding how on_toggle_caption, on_quit, on_hide_show work
- Modifying cluster_23-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `src/app_controller.py` | on_toggle_caption, on_quit, on_hide_show, on_mark_target, _new_meeting_id (+11) |

## Entry Points

Start here when exploring this area:

- **`on_toggle_caption`** (Function) — `src/app_controller.py:287`
- **`on_quit`** (Function) — `src/app_controller.py:290`
- **`on_hide_show`** (Function) — `src/app_controller.py:296`
- **`on_mark_target`** (Function) — `src/app_controller.py:299`
- **`start_new_session`** (Function) — `src/app_controller.py:625`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `on_toggle_caption` | Function | `src/app_controller.py` | 287 |
| `on_quit` | Function | `src/app_controller.py` | 290 |
| `on_hide_show` | Function | `src/app_controller.py` | 296 |
| `on_mark_target` | Function | `src/app_controller.py` | 299 |
| `start_new_session` | Function | `src/app_controller.py` | 625 |
| `open_session_history` | Function | `src/app_controller.py` | 642 |
| `_new_meeting_id` | Function | `src/app_controller.py` | 614 |
| `_session_display_name` | Function | `src/app_controller.py` | 617 |
| `_load_session_to_view` | Function | `src/app_controller.py` | 678 |
| `_toggle_caption` | Function | `src/app_controller.py` | 743 |
| `_toggle_detached_caption_panel` | Function | `src/app_controller.py` | 768 |
| `_toggle_live_input` | Function | `src/app_controller.py` | 780 |
| `_restore_main_panel` | Function | `src/app_controller.py` | 791 |
| `_minimize_to_floating` | Function | `src/app_controller.py` | 799 |
| `_mark_target_input` | Function | `src/app_controller.py` | 806 |
| `_notify` | Function | `src/app_controller.py` | 875 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `On_toggle → _notify` | cross_community | 5 |
| `_auto_start_capture → _notify` | cross_community | 4 |
| `_set_mode → _notify` | cross_community | 4 |
| `Open_session_history → Get` | cross_community | 3 |
| `Open_session_history → _notify` | intra_community | 3 |
| `Open_session_history → _session_display_name` | intra_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Ui | 2 calls |

## How to Explore

1. `gitnexus_context({name: "on_toggle_caption"})` — see callers and callees
2. `gitnexus_query({query: "cluster_23"})` — find related execution flows
3. Read key files listed above for implementation details
