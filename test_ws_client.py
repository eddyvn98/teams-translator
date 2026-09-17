import asyncio
import websockets
import json
import numpy as np

async def test_ws():
    uri = "ws://127.0.0.1:8000/ws/stream"
    print(f"Connecting to {uri}...")
    async with websockets.connect(uri) as ws:
        print("Connected!")
        # Send config
        await ws.send(json.dumps({
            "type": "config",
            "source_lang": "en",
            "target_lang": "vi"
        }))
        res = await ws.recv()
        print("Config response:", res)

        # Send text input test
        await ws.send(json.dumps({
            "type": "text_input",
            "text": "Hello world from websocket test."
        }))
        res1 = await ws.recv()
        print("Sentence event:", res1)
        res2 = await ws.recv()
        print("Transcript event:", res2)
        res3 = await ws.recv()
        print("Translation event:", res3)
        print("\nWebSocket test successful!")

if __name__ == "__main__":
    asyncio.run(test_ws())
