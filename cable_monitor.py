import sys
import time

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


def main() -> int:
    input_device = find_device("cable output", "input")
    output_device = find_device("wuying", "output")
    input_info = sd.query_devices(input_device)
    output_info = sd.query_devices(output_device)
    sample_rate = int(min(input_info["default_samplerate"], output_info["default_samplerate"]) or 48000)
    channels = 2

    print(
        f"Monitoring CABLE Output [{input_device}] -> Wuying speaker [{output_device}] "
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
