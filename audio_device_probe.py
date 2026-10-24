import json

import sounddevice as sd


def is_cable(name: str) -> bool:
    return "cable" in name.lower()


def score_device(device, host_name: str) -> int:
    name = device["name"].lower()
    score = 0
    if "wasapi" in host_name.lower():
        score += 5
    if "headset" in name:
        score += 8
    if "headphones" in name:
        score += 7
    if "bluetooth" in name:
        score += 6
    if "stereo" in name:
        score += 4
    if "speakers" in name:
        score += 4
    if "realtek" in name:
        score += 4
    if "fxsound" in name:
        score += 2
    return score


def main() -> int:
    current = None
    try:
        current_index = sd.default.device[1]
        if current_index is not None and int(current_index) >= 0:
            current = sd.query_devices(current_index)["name"]
    except Exception:
        current = None

    candidates = []
    for index, device in enumerate(sd.query_devices()):
        if device["max_output_channels"] <= 0:
            continue
        name = device["name"]
        if is_cable(name):
            continue
        host = sd.query_hostapis(device["hostapi"])["name"]
        candidates.append(
            {
                "index": index,
                "name": name,
                "score": score_device(device, host),
            }
        )

    best = None
    if candidates:
        candidates.sort(key=lambda item: (item["score"], item["index"], item["name"]), reverse=True)
        best = candidates[0]["name"]

    print(json.dumps({"current": current, "best": best}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
