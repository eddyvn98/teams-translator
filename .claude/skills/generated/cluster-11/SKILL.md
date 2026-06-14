---
name: cluster-11
description: "Skill for the Cluster_11 area of teams-translator. 4 symbols across 1 files."
---

# Cluster_11

4 symbols | 1 files | Cohesion: 86%

## When to Use

- Working with code in `src/`
- Understanding how listen_once work
- Modifying cluster_11-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `src/speech_to_text.py` | _get_recognizer, _listen_loop, listen_once, _is_key_pressed |

## Entry Points

Start here when exploring this area:

- **`listen_once`** (Function) — `src/speech_to_text.py:132`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `listen_once` | Function | `src/speech_to_text.py` | 132 |
| `_get_recognizer` | Function | `src/speech_to_text.py` | 34 |
| `_listen_loop` | Function | `src/speech_to_text.py` | 81 |
| `_is_key_pressed` | Function | `src/speech_to_text.py` | 154 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Cluster_9 | 1 calls |

## How to Explore

1. `gitnexus_context({name: "listen_once"})` — see callers and callees
2. `gitnexus_query({query: "cluster_11"})` — find related execution flows
3. Read key files listed above for implementation details
