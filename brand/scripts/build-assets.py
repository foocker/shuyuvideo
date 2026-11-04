"""Freeze local fonts, runtime and original sonic signatures for both intros.

Run from any directory: python brand/scripts/build-assets.py
Requires the repository's npm dependencies, numpy and fontTools[brotli].
"""
from pathlib import Path
import hashlib
import json
import shutil
import wave

import numpy as np
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from font_assets import build_subset

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
RATE = 48000
COPY = {
    "vendor/gsap.min.js": REPO / "node_modules/gsap/dist/gsap.min.js",
    "lib/omega-shape.js": REPO / "character/lib/omega-shape.js",
}
TEXT = "数语探索理性与想象的边界让更多人认识数学，参与数学。"


def signature(duration, full=False):
    # Original additive synthesis. No samples or reference-video audio.
    t = np.arange(round(duration * RATE)) / RATE
    channels = np.zeros((len(t), 2), dtype=np.float64)
    cues = [(0.12, 392.0, 0.13), (0.72, 523.251, 0.32), (1.44, 783.991, 0.27)]
    if full:
        cues += [(3.60, 659.255, 0.13), (4.34, 783.991, 0.15)]
    for i, (start, frequency, level) in enumerate(cues):
        u = np.maximum(0, t - start)
        env = (1 - np.exp(-u * 80)) * np.exp(-u * 5.2) * (t >= start)
        voice = (np.sin(2 * np.pi * frequency * u)
                 + 0.22 * np.sin(2 * np.pi * frequency * 2 * u) * np.exp(-u * 5)
                 + 0.07 * np.sin(2 * np.pi * frequency * 3 * u) * np.exp(-u * 10))
        mono = level * voice * env
        # Nearly centered, with one quiet deterministic reflection.
        pan = (-0.10, 0.04, 0.10)[i % 3]
        channels[:, 0] += mono * np.sqrt((1 - pan) / 2)
        channels[:, 1] += mono * np.sqrt((1 + pan) / 2)
        delay = round(0.065 * RATE)
        channels[delay:, 0] += mono[:-delay] * 0.07
        channels[delay:, 1] += mono[:-delay] * 0.09
    # Exact silent tail makes a clean cut into narration.
    fade_end = duration - 0.30
    fade = np.clip((fade_end - t) / 0.28, 0, 1)
    channels *= fade[:, None]
    return channels


def write_audio(path, samples):
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = (np.clip(samples, -1, 1) * 32767).round().astype("<i2")
    with wave.open(str(path), "wb") as out:
        out.setnchannels(2)
        out.setsampwidth(2)
        out.setframerate(RATE)
        out.writeframes(pcm.tobytes())


def main():
    extra_text = "".join(p.read_text(encoding="utf-8") for p in
                         [*ROOT.glob("compositions/*.html"), ROOT / "full/continuation.html"])
    for project in (ROOT, ROOT / "full"):
        assets = project / "assets"
        for relative, source in COPY.items():
            dest = assets / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)
        fonts = assets / "fonts"
        fonts.mkdir(parents=True, exist_ok=True)
        build_subset("sans-bold", TEXT + extra_text, fonts / "shuyu-brand.woff2")
    write_audio(ROOT / "assets/audio/brand-signature.wav", signature(3))
    write_audio(ROOT / "full/assets/audio/brand-full.wav", signature(7, full=True))
    intro = ROOT / "compositions/intro.html"
    if intro.exists():
        dest = ROOT / "full/compositions/intro.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        source = intro.read_text(encoding="utf-8")
        markup = (ROOT / "full/continuation.html").read_text(encoding="utf-8")
        animation = (ROOT / "full/continuation.js").read_text(encoding="utf-8")
        seam = "    </div>\n    <script>"
        end = "tl.set({}, {}, 3);"
        if source.count(seam) != 1 or source.count(end) != 1:
            raise RuntimeError("Intro source changed; update the continuation insertion points")
        source = source.replace('data-duration="3"', 'data-duration="7"')
        source = source.replace(seam, markup + "\n" + seam)
        source = source.replace(end, animation)
        dest.write_text(source, encoding="utf-8")
    manifest = {
        "omega": {"source": "../character/lib/omega-shape.js", "usage": "existing brand outline"},
        "font": {"source": "local Windows Microsoft YaHei Bold", "text": TEXT,
                 "distribution": "local build only; generated font subsets ignored by Git"},
        "audio": {"source": "scripts/build-assets.py", "method": "original additive synthesis, no samples",
                  "sample_rate": RATE, "channels": 2, "silent_tail_seconds": 0.3},
        "reference": {"source": "../../shuyuvideostudy/Backpropagation, intuitively ｜ Deep Learning Chapter 3 [Ilg3gGewQ5U].mp4",
                      "use": "timing and visual study of first 3.5 seconds only; no footage/audio in output"}
    }
    (ROOT / "assets/manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for relative in ("assets/audio/brand-signature.wav", "full/assets/audio/brand-full.wav"):
        path = ROOT / relative
        print(f"{relative}: {path.stat().st_size} bytes, sha256 {hashlib.sha256(path.read_bytes()).hexdigest()[:16]}")


if __name__ == "__main__":
    main()
