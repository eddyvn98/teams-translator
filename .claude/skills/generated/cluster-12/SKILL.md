---
name: cluster-12
description: "Skill for the Cluster_12 area of teams-translator. 5 symbols across 1 files."
---

# Cluster_12

5 symbols | 1 files | Cohesion: 80%

## When to Use

- Working with code in `src/`
- Understanding how generate_context_reply work
- Modifying cluster_12-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `src/reply_assistant.py` | _api_key, _base_url, _model, _chat, generate_context_reply |

## Entry Points

Start here when exploring this area:

- **`generate_context_reply`** (Function) — `src/reply_assistant.py:58`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `generate_context_reply` | Function | `src/reply_assistant.py` | 58 |
| `_api_key` | Function | `src/reply_assistant.py` | 14 |
| `_base_url` | Function | `src/reply_assistant.py` | 20 |
| `_model` | Function | `src/reply_assistant.py` | 27 |
| `_chat` | Function | `src/reply_assistant.py` | 34 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Generate_context_reply → _api_key` | intra_community | 3 |
| `Generate_context_reply → _base_url` | intra_community | 3 |
| `Generate_context_reply → _model` | intra_community | 3 |
| `Generate_context_reply → Get` | cross_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Ui | 2 calls |

## How to Explore

1. `gitnexus_context({name: "generate_context_reply"})` — see callers and callees
2. `gitnexus_query({query: "cluster_12"})` — find related execution flows
3. Read key files listed above for implementation details
