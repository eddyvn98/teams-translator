---
name: cluster-8
description: "Skill for the Cluster_8 area of teams-translator. 5 symbols across 1 files."
---

# Cluster_8

5 symbols | 1 files | Cohesion: 100%

## When to Use

- Working with code in `src/`
- Understanding how focus_teams, is_teams_focused, type_to_chat work
- Modifying cluster_8-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `src/teams_agent.py` | focus_teams, is_teams_focused, type_to_chat, send_message, _fallback_type |

## Entry Points

Start here when exploring this area:

- **`focus_teams`** (Function) — `src/teams_agent.py:49`
- **`is_teams_focused`** (Function) — `src/teams_agent.py:63`
- **`type_to_chat`** (Function) — `src/teams_agent.py:76`
- **`send_message`** (Function) — `src/teams_agent.py:108`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `focus_teams` | Function | `src/teams_agent.py` | 49 |
| `is_teams_focused` | Function | `src/teams_agent.py` | 63 |
| `type_to_chat` | Function | `src/teams_agent.py` | 76 |
| `send_message` | Function | `src/teams_agent.py` | 108 |
| `_fallback_type` | Function | `src/teams_agent.py` | 143 |

## How to Explore

1. `gitnexus_context({name: "focus_teams"})` — see callers and callees
2. `gitnexus_query({query: "cluster_8"})` — find related execution flows
3. Read key files listed above for implementation details
