"""Rebuild local study evidence. Requires ffmpeg, ffprobe, Pillow, numpy, matplotlib.

python scripts/build_evidence.py cases/backpropagation
Sampling is observational: it does not infer camera movement, musical instruments,
speech boundaries, or learning outcomes. Source captions remain a separate source.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


def stamp(t: float) -> str:
    return f"{int(t) // 60:02d}:{t % 60:05.2f}"


def run(cmd: list[str]) -> bytes:
    return subprocess.run(cmd, check=True, capture_output=True).stdout


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("case", type=Path)
    args = ap.parse_args()
    case = args.case.resolve()
    data = json.loads((case / "study.json").read_text(encoding="utf-8"))
    video = (case / data["video"]).resolve()
    if not video.is_file():
        raise FileNotFoundError(video)
    source = json.loads((case / "sources/provenance.json").read_text(encoding="utf-8"))
    with video.open("rb") as fp:
        digest = hashlib.file_digest(fp, "sha256").hexdigest()
    if digest != source["video"]["sha256"]:
        raise ValueError("Video changed; refresh provenance and review all timecodes first.")
    for record in source["sources"]:
        if hashlib.sha256((case / record["file"]).read_bytes()).hexdigest() != record["sha256"]:
            raise ValueError("Archived caption hash mismatch: " + record["file"])
    duration = float(source["probe"]["format"]["duration"])
    assert abs(data["duration"] - duration) < 0.05
    chapters = data["chapters"]
    assert chapters[0]["start"] == 0 and chapters[-1]["end"] == data["duration"]
    for i, chapter in enumerate(chapters):
        assert chapter["start"] < chapter["end"]
        if i:
            assert chapter["start"] == chapters[i - 1]["end"]
    for event in data["events"]:
        assert 0 <= event["start"] < event["end"] <= duration
        assert all(event["start"] <= t <= event["end"] for t in event["samples"]), event["id"]

    out = case / "evidence"
    out.mkdir(exist_ok=True)
    font_path = Path("C:/Windows/Fonts/consola.ttf")
    font = ImageFont.truetype(str(font_path), 17) if font_path.exists() else ImageFont.load_default()
    cache: dict[tuple[float, int], Image.Image] = {}
    manifest = {"video_sha256": digest, "time_labels": "Requested seek time in seconds; not a frame-accurate edit decision list.", "sheets": []}

    def frame(t: float, width: int) -> Image.Image:
        key = (t, width)
        if key not in cache:
            raw = run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", str(video),
                       "-frames:v", "1", "-vf", f"scale={width}:-2", "-f", "image2pipe", "-vcodec", "png", "-"])
            cache[key] = Image.open(io.BytesIO(raw)).convert("RGB")
        return cache[key]

    def sheet(name: str, times: list[float], width: int, cols: int) -> None:
        height = frame(times[0], width).height
        cell_h = height + 28
        im = Image.new("RGB", (cols * width, math.ceil(len(times) / cols) * cell_h), "#e6e5e0")
        draw = ImageDraw.Draw(im)
        for i, t in enumerate(times):
            x, y = i % cols * width, i // cols * cell_h
            im.paste(frame(t, width), (x, y + 28))
            draw.text((x + 8, y + 3), stamp(t), font=font, fill="#161a1e")
        im.save(out / name, quality=90)
        manifest["sheets"].append({"file": "evidence/" + name, "times": times, "width": im.width, "height": im.height})

    overview = list(range(5, math.floor(duration), 25))
    for page in range(math.ceil(len(overview) / 16)):
        sheet(f"overview-{page + 1}.jpg", overview[page * 16:(page + 1) * 16], 400, 4)
    for event in data["events"]:
        sheet(event["id"] + ".jpg", event["samples"], 640, 3)
        print("Evidence", event["id"], flush=True)
    for seq in data["sequences"]:
        count = round((seq["end"] - seq["start"]) * seq["fps"])
        times = [seq["start"] + i / seq["fps"] for i in range(count)]
        sheet(seq["id"] + ".jpg", times, 320, 6)
        print("Sequence", seq["id"], flush=True)

    # Caption boundaries are editorial timings, not measured voice activity.
    sentences = json.loads((case / "sources/sentence_timings.json").read_text(encoding="utf-8"))
    pcm = run(["ffmpeg", "-v", "error", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000", "-f", "f32le", "-"])
    samples = np.frombuffer(pcm, dtype="<f4")
    window = 1600  # 100 ms
    blocks = samples[:len(samples) // window * window].reshape(-1, window)
    rms = np.sqrt(np.mean(blocks.astype(np.float64) ** 2, axis=1))
    db = 20 * np.log10(np.maximum(rms, 1e-6))
    gaps = []
    for previous, following in zip(sentences, sentences[1:]):
        start, end = previous[2], following[1]
        if end - start >= 1:
            piece = db[math.floor(start * 10):math.ceil(end * 10)]
            gaps.append({"start": start, "end": end, "duration": round(end - start, 3),
                         "rms_dbfs_median": round(float(np.median(piece)), 2),
                         "classification": "caption_interval_only; not verified silence"})
    audio = {"method": "Original mix downmixed to mono, resampled to 16 kHz; RMS over non-overlapping 100 ms windows; 20*log10(RMS), floor -120 dBFS. Not LUFS or true peak.",
             "limits": "Cannot separate speech, music and sound effects. Caption gaps do not establish acoustic silence or deliberate pauses. No instruments, BPM, ducking or music cues inferred.",
             "sample_rate": 16000, "window_seconds": 0.1, "caption_gap_candidates": gaps,
             "rms_dbfs": np.round(db, 2).tolist()}
    (out / "audio-observations.json").write_text(json.dumps(audio, ensure_ascii=False, indent=2), encoding="utf-8")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(16, 3.4))
    t = np.arange(len(db)) * 0.1
    ax.plot(t, db, color="#26746e", linewidth=0.55, label="Original mix, 100 ms mono RMS")
    ax.axvspan(*data["focus"], color="#edc871", alpha=0.22, label="Detailed study 04:42-09:31")
    for sentence in sentences:
        ax.plot([sentence[1], sentence[2]], [-67, -67], color="#242b35", linewidth=3)
    ax.set_ylim(-72, 0)
    ticks = list(range(0, 781, 60))
    ax.set_xticks(ticks, [f"{v // 60:02d}:00" for v in ticks])
    ax.set_xlim(0, duration)
    ax.set_ylabel("dBFS (RMS)")
    ax.set_title("Mixed audio envelope; bottom bars = official sentence intervals, not voice detection")
    ax.grid(alpha=0.15)
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "audio-envelope.png", dpi=140)
    plt.close(fig)
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    # Classic local script works when index.html is opened directly with file://.
    (case / "study-data.js").write_text("// Generated by build_evidence.py; edit study.json instead.\nwindow.STUDY = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\nwindow.SENTENCES = " + json.dumps(sentences, ensure_ascii=False) + ";\n", encoding="utf-8")
    print(f"Built {len(manifest['sheets'])} sheets; {len(gaps)} caption gap candidates. {case}")


if __name__ == "__main__":
    main()
