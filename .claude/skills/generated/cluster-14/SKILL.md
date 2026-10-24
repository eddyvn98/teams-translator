---
name: cluster-14
description: "Skill for the Cluster_14 area of teams-translator. 12 symbols across 1 files."
---

# Cluster_14

12 symbols | 1 files | Cohesion: 96%

## When to Use

- Working with code in `src/`
- Understanding how register_session, append_transcript, upsert_minute_summary work
- Modifying cluster_14-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `src/meeting_store.py` | __init__, _connect, _init_db, register_session, append_transcript (+7) |

## Entry Points

Start here when exploring this area:

- **`register_session`** (Function) — `src/meeting_store.py:64`
- **`append_transcript`** (Function) — `src/meeting_store.py:90`
- **`upsert_minute_summary`** (Function) — `src/meeting_store.py:109`
- **`get_recent_transcripts`** (Function) — `src/meeting_store.py:129`
- **`get_recent_summaries`** (Function) — `src/meeting_store.py:143`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `register_session` | Function | `src/meeting_store.py` | 64 |
| `append_transcript` | Function | `src/meeting_store.py` | 90 |
| `upsert_minute_summary` | Function | `src/meeting_store.py` | 109 |
| `get_recent_transcripts` | Function | `src/meeting_store.py` | 129 |
| `get_recent_summaries` | Function | `src/meeting_store.py` | 143 |
| `get_transcript_range` | Function | `src/meeting_store.py` | 157 |
| `get_transcripts_by_meeting` | Function | `src/meeting_store.py` | 171 |
| `get_latest_summary_by_meeting` | Function | `src/meeting_store.py` | 188 |
| `list_sessions` | Function | `src/meeting_store.py` | 205 |
| `__init__` | Function | `src/meeting_store.py` | 10 |
| `_connect` | Function | `src/meeting_store.py` | 18 |
| `_init_db` | Function | `src/meeting_store.py` | 23 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Ui | 1 calls |

## How to Explore

1. `gitnexus_context({name: "register_session"})` — see callers and callees
2. `gitnexus_query({query: "cluster_14"})` — find related execution flows
3. Read key files listed above for implementation details
