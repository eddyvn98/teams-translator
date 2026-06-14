---
name: ui
description: "Skill for the Ui area of teams-translator. 55 symbols across 15 files."
---

# Ui

55 symbols | 15 files | Cohesion: 87%

## When to Use

- Working with code in `src/`
- Understanding how main, on_event, list_loopback_devices work
- Modifying ui-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `src/ui/live_input_window.py` | _on_caption_update, translate_and_inject, generate_reply_from_vn, generate_auto_reply, speak_reply (+13) |
| `src/app_controller.py` | _summary_worker, generate_reply_from_vietnamese, generate_auto_reply, _generate_contextual_reply, speak_english_reply (+5) |
| `src/loopback_capture.py` | list_loopback_devices, find_best_loopback_device, capture_once, LoopbackCapture, __init__ |
| `src/ui/floating_controls.py` | FloatingControlWidget, __init__, _build_ui, _make_button, _apply_style |
| `src/caption_window.py` | _on_update_text, _get_opacity, _check_fade, CaptionWindow |
| `src/text_to_speech.py` | on_event, TextToSpeech |
| `src/config_manager.py` | get, ConfigManager |
| `src/speech_to_text.py` | SpeechToText, __init__ |
| `src/whisper_subprocess.py` | main |
| `src/ui/settings_window.py` | __init__ |

## Entry Points

Start here when exploring this area:

- **`main`** (Function) — `src/whisper_subprocess.py:11`
- **`on_event`** (Function) — `src/text_to_speech.py:110`
- **`list_loopback_devices`** (Function) — `src/loopback_capture.py:49`
- **`find_best_loopback_device`** (Function) — `src/loopback_capture.py:88`
- **`capture_once`** (Function) — `src/loopback_capture.py:280`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `Translator` | Class | `src/translator.py` | 12 |
| `TextToSpeech` | Class | `src/text_to_speech.py` | 16 |
| `TeamsAgent` | Class | `src/teams_agent.py` | 13 |
| `SpeechToText` | Class | `src/speech_to_text.py` | 16 |
| `ReplyAssistant` | Class | `src/reply_assistant.py` | 10 |
| `QwenSTT` | Class | `src/qwen_stt.py` | 14 |
| `MeetingStore` | Class | `src/meeting_store.py` | 7 |
| `LoopbackCapture` | Class | `src/loopback_capture.py` | 24 |
| `ConfigManager` | Class | `src/config_manager.py` | 78 |
| `CaptionWindow` | Class | `src/caption_window.py` | 24 |
| `LiveInputWindow` | Class | `src/ui/live_input_window.py` | 23 |
| `FloatingControlWidget` | Class | `src/ui/floating_controls.py` | 4 |
| `main` | Function | `src/whisper_subprocess.py` | 11 |
| `on_event` | Function | `src/text_to_speech.py` | 110 |
| `list_loopback_devices` | Function | `src/loopback_capture.py` | 49 |
| `find_best_loopback_device` | Function | `src/loopback_capture.py` | 88 |
| `capture_once` | Function | `src/loopback_capture.py` | 280 |
| `get` | Function | `src/config_manager.py` | 101 |
| `generate_reply_from_vietnamese` | Function | `src/app_controller.py` | 696 |
| `generate_auto_reply` | Function | `src/app_controller.py` | 704 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Speak → Get` | cross_community | 6 |
| `On_toggle → Get` | cross_community | 4 |
| `_speak_qwen_rest → Get` | cross_community | 4 |
| `Open_session_history → Get` | cross_community | 3 |
| `Generate_context_reply → Get` | cross_community | 3 |
| `Generate_reply_from_vietnamese → Get` | intra_community | 3 |
| `Generate_auto_reply → Get` | intra_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Cluster_23 | 2 calls |
| Cluster_21 | 1 calls |

## How to Explore

1. `gitnexus_context({name: "main"})` — see callers and callees
2. `gitnexus_query({query: "ui"})` — find related execution flows
3. Read key files listed above for implementation details
