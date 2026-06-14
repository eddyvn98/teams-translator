import argparse
import sys
import time
from typing import Optional

import sounddevice as sd


def find_device(name_part: str, kind: str, preferred_host: str = "WASAPI") -> int:
    name_part = name_part.lower()
    fallback = None
    for index, device in enumerate(sd.query_devices()):
        host = sd.query_hostapis(device["hostapi"])["name"]
        name = device["name"].lower()
        has_channels = (
            device["max_input_channels"] > 0
            if kind == "input"
            else device["max_output_channels"] > 0
        )
        if name_part in name and has_channels:
            if preferred_host.lower() in host.lower():
                return index
            if fallback is None:
                fallback = index
    if fallback is not None:
        return fallback
    raise RuntimeError(f"Device not found: {name_part} ({kind})")


def find_best_output_device(preferred_host: str = "WASAPI", preferred_device: Optional[str] = None) -> int:
    candidates = []
    preferred_exact = None
    preferred_partial = None
    fallback_exact = None
    fallback_partial = None
    for index, device in enumerate(sd.query_devices()):
        if device["max_output_channels"] <= 0:
            continue
        host = sd.query_hostapis(device["hostapi"])["name"]
        name = device["name"].lower()
        if "cable" in name:
            continue

        if preferred_device:
            preferred_lower = preferred_device.strip().lower()
            if name == preferred_lower:
                if preferred_host.lower() in host.lower():
                    return index
                if fallback_exact is None:
                    fallback_exact = index
            elif preferred_lower in name and preferred_partial is None:
                if preferred_host.lower() in host.lower():
                    preferred_partial = index
                elif fallback_partial is None:
                    fallback_partial = index
            # Keep evaluating scoring so we have a fallback if no preferred match exists.

        score = 0
        if preferred_host.lower() in host.lower():
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
        if "hands-free" in name or "hands free" in name:
            score -= 3
        candidates.append((score, index, device["name"], host))

    if preferred_partial is not None:
        return preferred_partial
    if fallback_exact is not None:
        return fallback_exact
    if fallback_partial is not None:
        return fallback_partial

    if not candidates:
        raise RuntimeError("No non-cable output device found")

    preferred_candidates = [item for item in candidates if preferred_host.lower() in item[3].lower()]
    if preferred_candidates:
        candidates = preferred_candidates

    candidates.sort(reverse=True)
    return candidates[0][1]


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--output-device", dest="output_device", default=None)
    args, _ = parser.parse_known_args()

    input_device = find_device("cable output", "input")
    output_device = find_best_output_device(preferred_device=args.output_device)
    input_info = sd.query_devices(input_device)
    output_info = sd.query_devices(output_device)
    sample_rate = int(min(input_info["default_samplerate"], output_info["default_samplerate"]) or 48000)
    channels = 2

    print(
        f"Monitoring CABLE Output [{input_device}] -> {output_info['name']} [{output_device}] "
        f"at {sample_rate}Hz",
        flush=True,
    )

    with sd.Stream(
        samplerate=sample_rate,
        blocksize=1024,
        dtype="float32",
        channels=channels,
        device=(input_device, output_device),
        latency="low",
        callback=lambda indata, outdata, frames, time_info, status: outdata.__setitem__(slice(None), indata),
    ):
        while True:
            time.sleep(1)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(0)
    except Exception as exc:
        print(f"Audio monitor failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
