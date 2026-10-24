---
name: cluster-13
description: "Skill for the Cluster_13 area of teams-translator. 7 symbols across 1 files."
---

# Cluster_13

7 symbols | 1 files | Cohesion: 88%

## When to Use

- Working with code in `src/`
- Understanding how transcribe_audio, summarize_text work
- Modifying cluster_13-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `src/qwen_stt.py` | _api_key, _base_url, _model, _to_wav_bytes, _fallback_model (+2) |

## Entry Points

Start here when exploring this area:

- **`transcribe_audio`** (Function) — `src/qwen_stt.py:69`
- **`summarize_text`** (Function) — `src/qwen_stt.py:151`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `transcribe_audio` | Function | `src/qwen_stt.py` | 69 |
| `summarize_text` | Function | `src/qwen_stt.py` | 151 |
| `_api_key` | Function | `src/qwen_stt.py` | 18 |
| `_base_url` | Function | `src/qwen_stt.py` | 26 |
| `_model` | Function | `src/qwen_stt.py` | 36 |
| `_to_wav_bytes` | Function | `src/qwen_stt.py` | 51 |
| `_fallback_model` | Function | `src/qwen_stt.py` | 63 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Ui | 2 calls |

## How to Explore

1. `gitnexus_context({name: "transcribe_audio"})` — see callers and callees
2. `gitnexus_query({query: "cluster_13"})` — find related execution flows
3. Read key files listed above for implementation details
