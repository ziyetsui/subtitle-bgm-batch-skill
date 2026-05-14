---
name: subtitle-bgm-batch
description: Batch add Chinese subtitles and background music to videos. Use when the user provides raw videos or a folder of videos and asks Codex to add subtitles, burn captions, add/mix BGM, use the video editing SOP, batch process CleanShot recordings, or output ready-to-publish captioned videos.
---

# Subtitle + BGM Batch

## Purpose

Use this skill for the narrow workflow: raw video(s) in, Chinese subtitles plus the bundled background music out. Do not remove filler words, trim clips, rewrite scripts, or perform publishing steps unless the user explicitly asks for extra work.

## Default Workflow

1. Put source videos in a working input folder, or use the paths the user provides directly.
2. Run `scripts/add_subtitle_bgm_batch.py` with the video paths or folder.
3. Save outputs in `output_subtitle_bgm` next to the input folder unless the user gives an output directory.
4. Report the output directory and any failed files.

## Command

```bash
python3 /Users/ziye/.codex/skills/subtitle-bgm-batch/scripts/add_subtitle_bgm_batch.py \
  --input /path/to/video_or_folder \
  --output /path/to/output_folder
```

If multiple files are provided:

```bash
python3 /Users/ziye/.codex/skills/subtitle-bgm-batch/scripts/add_subtitle_bgm_batch.py \
  --input video1.mp4 video2.mov \
  --output /path/to/output_folder
```

## Behavior

- Uses Whisper to transcribe Chinese speech and create subtitle segments.
- Burns subtitles into the video as yellow text with black outline.
- Mixes the original audio with `assets/bgm.mp3`, or another MP3 passed with `--bgm`.
- Writes files as `<original_stem>_subtitle_bgm.mp4`.
- Skips existing outputs unless `--overwrite` is set.
- Stores transcript JSON sidecars in `<output>/transcripts`.

## Defaults

- Whisper model: `medium`
- Original audio volume: `1.5`
- BGM volume: `0.12`
- Subtitle font: `/System/Library/Fonts/STHeiti Medium.ttc`
- Supported input extensions: `.mp4`, `.mov`, `.m4v`

## Checks Before Running

Verify these commands work:

```bash
ffmpeg -version
ffprobe -version
python3 -c 'import whisper, PIL; print("ok")'
```

If Whisper or Pillow is missing, tell the user the missing dependency before processing. If the user wants you to install it, request approval because dependency installation needs network access.

## BGM Asset

For the local skill on this Mac, the BGM is stored at:

```text
/Users/ziye/.codex/skills/subtitle-bgm-batch/assets/bgm.mp3
```

The BGM file is intentionally excluded from Git because it is larger than GitHub's normal 100MB file limit. After cloning this skill elsewhere, either place a local `bgm.mp3` in `assets/` or pass a music file explicitly:

```bash
python3 /path/to/add_subtitle_bgm_batch.py --input /path/to/videos --bgm /path/to/bgm.mp3
```

## Notes

- The bundled BGM came from the user's SOP folder: `/Users/ziye/Desktop/视频剪辑/01_待剪辑/90_SOP/bgm.mp3`.
- Use the bundled script instead of re-implementing ffmpeg commands manually.
- For long videos or many inputs, process in batches and keep the user updated because Whisper and video rendering can take time.
