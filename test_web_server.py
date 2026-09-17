"""
Test suite for Teams Translator Web Server
"""

import asyncio
import json
from fastapi.testclient import TestClient
from src_web.server import app

client = TestClient(app)

def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "asr_url" in data

def test_static_index():
    res = client.get("/")
    assert res.status_code == 200
    assert "Google AI Studio" in res.text

def test_config_endpoints():
    res = client.get("/api/config")
    assert res.status_code == 200
    data = res.json()
    assert "target_language" in data
    assert "source_language" in data

def test_translate_endpoint():
    res = client.post(
        "/api/translate",
        json={"text": "Hello world", "source_lang": "en", "target_lang": "vi"}
    )
    assert res.status_code == 200
    data = res.json()
    assert "translated" in data
    assert len(data["translated"]) > 0
    print("Translated output:", data["translated"])

def test_websocket_stream():
    with client.websocket_connect("/ws/stream") as ws:
        # Send config
        ws.send_json({
            "type": "config",
            "source_lang": "en",
            "target_lang": "vi"
        })
        resp = ws.receive_json()
        assert resp["type"] == "status"

        # Send text input for translation
        ws.send_json({
            "type": "text_input",
            "text": "Welcome to our meeting today."
        })
        resp_sentence = ws.receive_json()
        assert resp_sentence["type"] == "sentence"
        assert resp_sentence["source"] == "Welcome to our meeting today."
        assert len(resp_sentence["translated"]) > 0

        resp_transcript = ws.receive_json()
        assert resp_transcript["type"] == "transcript"

        resp_translation = ws.receive_json()
        assert resp_translation["type"] == "translation"
        print("WS Translation result:", resp_sentence["translated"])

if __name__ == "__main__":
    print("Testing health...")
    test_health()
    print("Testing static frontend...")
    test_static_index()
    print("Testing config...")
    test_config_endpoints()
    print("Testing translation...")
    test_translate_endpoint()
    print("Testing WebSocket stream...")
    test_websocket_stream()
    print("\nAll tests passed successfully!")
