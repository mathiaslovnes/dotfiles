#!/usr/bin/python3
"""Prints SoundSource's Output EQ (Apple's AUNBandEQ) as an ffmpeg filter chain for mpv, or
nothing if mpv isn't excluded in SoundSource (then SoundSource applies the EQ itself).

Read fresh from SoundSource's settings every time mpv starts, so mpv follows any change you
make to the EQ in SoundSource."""
import os
import plistlib
import struct
import subprocess

SOURCES = os.path.expanduser("~/Library/Application Support/SoundSource/Sources.plist")
TYPES = {  # AUNBandEQ filter type -> ffmpeg filter (width in octaves where the type has one)
    0: "equalizer", 1: "lowpass", 2: "highpass", 3: "lowpass", 4: "highpass", 5: "bandpass",
    6: "bandreject", 7: "lowshelf", 8: "highshelf", 9: "lowshelf", 10: "highshelf",
}
HAS_WIDTH = {0, 3, 4, 5, 6, 9, 10}
HAS_GAIN = {0, 7, 8, 9, 10}


def mpv_excluded():
    out = subprocess.run(["/usr/bin/defaults", "read", "com.rogueamoeba.soundsource", "SSAudioExclusions"],
                         capture_output=True, text=True).stdout
    return "io.mpv" in out


def output_eq():
    with open(SOURCES, "rb") as f:
        sources = plistlib.load(f)
    out = next(m for m in sources["modelItems"] if m.get("infoKey") == "OutputSource")
    if out.get("effectsDisabled"):
        return []
    filters = []
    for effect in out.get("effects", []):
        props = effect.get("nodeProperties", {})
        if not effect.get("enabled", True) or props.get("bypassed") or props.get("audioUnitUid") != "aufx.appl.nbeq":
            continue
        blob = props["audioUnitSettings"]["data"]
        p, i = {}, 0
        while i + 12 <= len(blob):
            scope, _element, count = struct.unpack(">III", blob[i:i + 12])
            i += 12
            for _ in range(count):
                pid, val = struct.unpack(">If", blob[i:i + 8])
                i += 8
                if scope == 0:
                    p[pid] = val
        if p.get(0):
            filters.append(f"volume={p[0]:.2f}dB")
        for band in range(props["audioUnitSettings"].get("numberOfBands", 0)):
            if 3000 + band not in p or p.get(1000 + band):
                continue
            kind = int(p.get(2000 + band, 0))
            f = f"{TYPES[kind]}=f={p[3000 + band]:.1f}"
            if kind in HAS_GAIN:
                f += f":g={p.get(4000 + band, 0):.2f}"
            if kind in HAS_WIDTH:
                f += f":t=o:w={p.get(5000 + band, 1):.3f}"
            filters.append(f)
    return filters


if __name__ == "__main__":
    try:
        if mpv_excluded():
            print(",".join(output_eq()))
    except Exception:  # never break playback over this
        print("")
