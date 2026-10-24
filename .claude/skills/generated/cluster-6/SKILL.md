---
name: cluster-6
description: "Skill for the Cluster_6 area of teams-translator. 5 symbols across 1 files."
---

# Cluster_6

5 symbols | 1 files | Cohesion: 67%

## When to Use

- Working with code in `src/`
- Understanding how speak, stop work
- Modifying cluster_6-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `src/text_to_speech.py` | speak, _do_speak, _speak_pyttsx3, _apply_pyttsx3_config, stop |

## Entry Points

Start here when exploring this area:

- **`speak`** (Function) — `src/text_to_speech.py:25`
- **`stop`** (Function) — `src/text_to_speech.py:293`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `speak` | Function | `src/text_to_speech.py` | 25 |
| `stop` | Function | `src/text_to_speech.py` | 293 |
| `_do_speak` | Function | `src/text_to_speech.py` | 30 |
| `_speak_pyttsx3` | Function | `src/text_to_speech.py` | 248 |
| `_apply_pyttsx3_config` | Function | `src/text_to_speech.py` | 265 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Speak → _config_value` | cross_community | 6 |
| `Speak → Get` | cross_community | 6 |
| `Speak → _api_key` | cross_community | 5 |
| `Speak → RealtimeCallback` | cross_community | 5 |
| `Speak → _apply_pyttsx3_config` | intra_community | 4 |
| `Speak → Stop` | intra_community | 4 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Cluster_7 | 2 calls |
| Cluster_9 | 1 calls |

## How to Explore

1. `gitnexus_context({name: "speak"})` — see callers and callees
2. `gitnexus_query({query: "cluster_6"})` — find related execution flows
3. Read key files listed above for implementation details
