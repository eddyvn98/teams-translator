---
name: cluster-0
description: "Skill for the Cluster_0 area of teams-translator. 13 symbols across 3 files."
---

# Cluster_0

13 symbols | 3 files | Cohesion: 97%

## When to Use

- Working with code in `src/`
- Understanding how on_speech, detect_language, translate work
- Modifying cluster_0-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `src/translator.py` | _config_value, _timeout, _normalize_text, _cache_get, _cache_set (+6) |
| `test_full_flow.py` | on_speech |
| `src/caption_window.py` | show_caption |

## Entry Points

Start here when exploring this area:

- **`on_speech`** (Function) — `test_full_flow.py:31`
- **`detect_language`** (Function) — `src/translator.py:158`
- **`translate`** (Function) — `src/translator.py:180`
- **`translate_bidirectional`** (Function) — `src/translator.py:242`
- **`show_caption`** (Function) — `src/caption_window.py:257`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `on_speech` | Function | `test_full_flow.py` | 31 |
| `detect_language` | Function | `src/translator.py` | 158 |
| `translate` | Function | `src/translator.py` | 180 |
| `translate_bidirectional` | Function | `src/translator.py` | 242 |
| `show_caption` | Function | `src/caption_window.py` | 257 |
| `_config_value` | Function | `src/translator.py` | 23 |
| `_timeout` | Function | `src/translator.py` | 26 |
| `_normalize_text` | Function | `src/translator.py` | 32 |
| `_cache_get` | Function | `src/translator.py` | 35 |
| `_cache_set` | Function | `src/translator.py` | 41 |
| `_get_translator` | Function | `src/translator.py` | 53 |
| `_google_translate_via_requests` | Function | `src/translator.py` | 66 |
| `_qwen_translate_en_vi` | Function | `src/translator.py` | 99 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `On_speech → _config_value` | intra_community | 5 |
| `Translate_bidirectional → _config_value` | intra_community | 5 |
| `On_speech → _normalize_text` | intra_community | 3 |
| `On_speech → _cache_get` | intra_community | 3 |
| `Translate_bidirectional → _normalize_text` | intra_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Ui | 1 calls |

## How to Explore

1. `gitnexus_context({name: "on_speech"})` — see callers and callees
2. `gitnexus_query({query: "cluster_0"})` — find related execution flows
3. Read key files listed above for implementation details
