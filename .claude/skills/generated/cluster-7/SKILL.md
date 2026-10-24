---
name: cluster-7
description: "Skill for the Cluster_7 area of teams-translator. 9 symbols across 1 files."
---

# Cluster_7

9 symbols | 1 files | Cohesion: 79%

## When to Use

- Working with code in `src/`
- Understanding how RealtimeCallback work
- Modifying cluster_7-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `src/text_to_speech.py` | _config_value, _api_key, _speak_qwen, _speak_qwen_realtime, RealtimeCallback (+4) |

## Entry Points

Start here when exploring this area:

- **`RealtimeCallback`** (Class) — `src/text_to_speech.py:104`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `RealtimeCallback` | Class | `src/text_to_speech.py` | 104 |
| `_config_value` | Function | `src/text_to_speech.py` | 56 |
| `_api_key` | Function | `src/text_to_speech.py` | 59 |
| `_speak_qwen` | Function | `src/text_to_speech.py` | 65 |
| `_speak_qwen_realtime` | Function | `src/text_to_speech.py` | 78 |
| `_text_chunks` | Function | `src/text_to_speech.py` | 155 |
| `_speak_qwen_rest` | Function | `src/text_to_speech.py` | 159 |
| `_play_wav` | Function | `src/text_to_speech.py` | 209 |
| `_find_output_device` | Function | `src/text_to_speech.py` | 231 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Speak → _config_value` | cross_community | 6 |
| `Speak → Get` | cross_community | 6 |
| `Speak → _api_key` | cross_community | 5 |
| `Speak → RealtimeCallback` | cross_community | 5 |
| `_speak_qwen_rest → _config_value` | intra_community | 4 |
| `_speak_qwen_rest → Get` | cross_community | 4 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Ui | 3 calls |
| Cluster_9 | 1 calls |
| Cluster_6 | 1 calls |

## How to Explore

1. `gitnexus_context({name: "RealtimeCallback"})` — see callers and callees
2. `gitnexus_query({query: "cluster_7"})` — find related execution flows
3. Read key files listed above for implementation details
