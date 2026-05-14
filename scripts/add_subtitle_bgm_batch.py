#!/usr/bin/env python3
"""
Batch add burned Chinese subtitles and background music to videos.

Inputs can be video files or directories. Directories are scanned one level by
default, recursively when --recursive is set.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


VIDEO_EXTS = {".mp4", ".mov", ".m4v"}
DEFAULT_MODEL = "medium"
DEFAULT_ORIG_VOLUME = 1.5
DEFAULT_BGM_VOLUME = 0.12
DEFAULT_FONT = "/System/Library/Fonts/STHeiti Medium.ttc"
DEFAULT_MARGIN_RATIO = 24


def log(message: str) -> None:
    print(message, flush=True)


def require_command(name: str) -> None:
    if not shutil.which(name):
        raise RuntimeError(f"Missing required command: {name}")


def check_python_deps() -> None:
    missing = []
    try:
        import whisper  # noqa: F401
    except Exception:
        missing.append("whisper")
    try:
        import PIL  # noqa: F401
    except Exception:
        missing.append("Pillow")
    if missing:
        raise RuntimeError(
            "Missing Python dependencies: "
            + ", ".join(missing)
            + ". Install them before running this skill."
        )


def collect_videos(inputs: list[str], recursive: bool) -> list[Path]:
    videos: list[Path] = []
    for item in inputs:
        path = Path(item).expanduser().resolve()
        if path.is_file() and path.suffix.lower() in VIDEO_EXTS:
            videos.append(path)
        elif path.is_dir():
            iterator = path.rglob("*") if recursive else path.glob("*")
            videos.extend(
                p.resolve()
                for p in iterator
                if p.is_file() and p.suffix.lower() in VIDEO_EXTS
            )
        else:
            log(f"[skip] Not a supported video or directory: {path}")
    return sorted(dict.fromkeys(videos))


def ffprobe_info(video: Path) -> dict:
    raw = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_streams",
            "-show_format",
            str(video),
        ]
    )
    data = json.loads(raw)
    duration = float(data["format"]["duration"])
    for stream in data["streams"]:
        if stream.get("codec_type") == "video":
            fps_str = stream.get("avg_frame_rate") or stream.get("r_frame_rate") or "25/1"
            if fps_str == "0/0":
                fps_str = stream.get("r_frame_rate") or "25/1"
            num, den = fps_str.split("/")
            fps = float(num) / float(den)
            return {
                "duration": duration,
                "width": int(stream["width"]),
                "height": int(stream["height"]),
                "fps": fps,
                "fps_str": fps_str,
            }
    raise RuntimeError(f"No video stream found: {video}")


def extract_audio(video: Path, wav: Path) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(video),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-acodec",
            "pcm_s16le",
            str(wav),
        ],
        check=True,
    )


def transcribe_audio(wav: Path, model_name: str) -> list[dict]:
    import whisper

    model = whisper.load_model(model_name)
    result = model.transcribe(str(wav), language="zh", word_timestamps=False)
    segments = []
    for seg in result.get("segments", []):
        text = str(seg.get("text", "")).strip()
        if not text:
            continue
        segments.append(
            {
                "text": text,
                "start": round(float(seg["start"]), 3),
                "end": round(float(seg["end"]), 3),
            }
        )
    return segments


def write_transcript(path: Path, video: Path, info: dict, segments: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "video": str(video),
        "duration": info["duration"],
        "width": info["width"],
        "height": info["height"],
        "fps": info["fps"],
        "fps_str": info["fps_str"],
        "segments": segments,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def wrap_text(draw, text: str, font, max_width: int) -> list[str]:
    chars = list(text.strip())
    lines: list[str] = []
    current = ""
    for char in chars:
        trial = current + char
        bbox = draw.textbbox((0, 0), trial, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = char
    if current:
        lines.append(current)
    return lines[:2]


def create_subtitle_png(
    text: str,
    width: int,
    height: int,
    font_path: str,
    path: Path,
) -> None:
    from PIL import Image, ImageDraw, ImageFont

    font_size = max(32, height // 28)
    font = ImageFont.truetype(font_path, font_size)
    probe = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    draw = ImageDraw.Draw(probe)
    lines = wrap_text(draw, text, font, int(width * 0.88))
    if not lines:
        Image.new("RGBA", (1, 1), (0, 0, 0, 0)).save(path)
        return

    line_height = int(font_size * 1.18)
    outline = 3
    text_width = max(
        draw.textbbox((0, 0), line, font=font)[2]
        - draw.textbbox((0, 0), line, font=font)[0]
        for line in lines
    )
    img_width = text_width + outline * 2 + 8
    img_height = line_height * len(lines) + outline * 2 + 8
    image = Image.new("RGBA", (img_width, img_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    y = outline + 4
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_width = bbox[2] - bbox[0]
        x = (img_width - line_width) // 2
        for dx in range(-outline, outline + 1):
            for dy in range(-outline, outline + 1):
                if dx or dy:
                    draw.text((x + dx, y + dy), line, font=font, fill=(0, 0, 0, 255))
        draw.text((x, y), line, font=font, fill=(255, 255, 0, 255))
        y += line_height

    image.save(path)


def build_overlays(
    segments: list[dict],
    info: dict,
    font_path: str,
    tmp_dir: Path,
) -> list[tuple[Path, float, float]]:
    overlays = []
    for idx, seg in enumerate(segments):
        png = tmp_dir / f"sub_{idx:04d}.png"
        create_subtitle_png(seg["text"], info["width"], info["height"], font_path, png)
        overlays.append((png, float(seg["start"]), float(seg["end"])))
    return overlays


def render_video(
    src: Path,
    dst: Path,
    info: dict,
    segments: list[dict],
    bgm: Path,
    font_path: str,
    original_volume: float,
    bgm_volume: float,
) -> None:
    margin = max(50, int(info["height"]) // DEFAULT_MARGIN_RATIO)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        overlays = build_overlays(segments, info, font_path, tmp_path)

        inputs = ["-i", str(src)]
        for png, _, _ in overlays:
            inputs += ["-loop", "1", "-i", str(png)]

        bgm_input_index = None
        if bgm.exists():
            bgm_input_index = 1 + len(overlays)
            inputs += ["-stream_loop", "-1", "-i", str(bgm)]

        filters = [f"[0:v]fps={info['fps_str']}[v0]"]
        current = "v0"
        for idx, (_, start, end) in enumerate(overlays, start=1):
            out = f"v{idx}"
            filters.append(
                f"[{current}][{idx}:v]overlay="
                f"x=(main_w-overlay_w)/2:y=main_h-overlay_h-{margin}:"
                f"enable='between(t,{start:.3f},{end:.3f})'[{out}]"
            )
            current = out

        if bgm_input_index is not None:
            filters.append(f"[0:a]volume={original_volume}[voice]")
            filters.append(f"[{bgm_input_index}:a]volume={bgm_volume}[bgm]")
            filters.append("[voice][bgm]amix=inputs=2:duration=first:dropout_transition=2[a]")
        else:
            filters.append(f"[0:a]volume={original_volume}[a]")

        cmd = (
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
            + inputs
            + [
                "-filter_complex",
                ";".join(filters),
                "-map",
                f"[{current}]",
                "-map",
                "[a]",
                "-c:v",
                "libx264",
                "-crf",
                "18",
                "-preset",
                "fast",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-shortest",
                str(dst),
            ]
        )
        subprocess.run(cmd, check=True)


def process_one(video: Path, args: argparse.Namespace, output_dir: Path, transcript_dir: Path) -> bool:
    dst = output_dir / f"{video.stem}_subtitle_bgm.mp4"
    transcript = transcript_dir / f"{video.stem}_transcription.json"
    if dst.exists() and not args.overwrite:
        log(f"[skip] Exists: {dst}")
        return True

    log(f"\n==> {video.name}")
    try:
        info = ffprobe_info(video)
        log(f"    {info['width']}x{info['height']} @ {info['fps']:.2f}fps, {info['duration']:.1f}s")
        with tempfile.TemporaryDirectory() as tmp:
            wav = Path(tmp) / "audio.wav"
            log("    extract audio")
            extract_audio(video, wav)
            log(f"    transcribe with Whisper {args.model}")
            segments = transcribe_audio(wav, args.model)
        log(f"    subtitle segments: {len(segments)}")
        write_transcript(transcript, video, info, segments)
        log("    render subtitles + bgm")
        render_video(
            video,
            dst,
            info,
            segments,
            args.bgm,
            args.font,
            args.original_volume,
            args.bgm_volume,
        )
        log(f"    done: {dst}")
        return True
    except Exception as exc:
        log(f"[error] {video}: {exc}")
        return False


def parse_args() -> argparse.Namespace:
    skill_dir = Path(__file__).resolve().parents[1]
    default_bgm = skill_dir / "assets" / "bgm.mp3"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", nargs="+", required=True, help="Video file(s) or folder(s).")
    parser.add_argument("--output", help="Output folder. Defaults to input folder/output_subtitle_bgm.")
    parser.add_argument("--recursive", action="store_true", help="Scan input folders recursively.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing output files.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Whisper model name.")
    parser.add_argument("--bgm", type=Path, default=default_bgm, help="Background music mp3.")
    parser.add_argument("--font", default=DEFAULT_FONT, help="Subtitle font path.")
    parser.add_argument("--original-volume", type=float, default=DEFAULT_ORIG_VOLUME)
    parser.add_argument("--bgm-volume", type=float, default=DEFAULT_BGM_VOLUME)
    return parser.parse_args()


def default_output_dir(inputs: list[str]) -> Path:
    first = Path(inputs[0]).expanduser().resolve()
    base = first if first.is_dir() else first.parent
    return base / "output_subtitle_bgm"


def main() -> int:
    args = parse_args()
    require_command("ffmpeg")
    require_command("ffprobe")
    check_python_deps()

    args.bgm = args.bgm.expanduser().resolve()
    if not args.bgm.exists():
        raise RuntimeError(f"BGM not found: {args.bgm}")
    if not Path(args.font).exists():
        raise RuntimeError(f"Font not found: {args.font}")

    videos = collect_videos(args.input, args.recursive)
    if not videos:
        log("No supported input videos found.")
        return 1

    output_dir = Path(args.output).expanduser().resolve() if args.output else default_output_dir(args.input)
    transcript_dir = output_dir / "transcripts"
    output_dir.mkdir(parents=True, exist_ok=True)
    transcript_dir.mkdir(parents=True, exist_ok=True)

    log(f"videos: {len(videos)}")
    log(f"output: {output_dir}")
    log(f"bgm: {args.bgm}")

    ok = 0
    for video in videos:
        if process_one(video, args, output_dir, transcript_dir):
            ok += 1

    log(f"\nfinished: {ok}/{len(videos)} succeeded")
    return 0 if ok == len(videos) else 2


if __name__ == "__main__":
    sys.exit(main())
