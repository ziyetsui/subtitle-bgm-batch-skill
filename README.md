# subtitle-bgm-batch-skill

[中文文档](README-zh_CN.md) | **English**

**Subtitle + BGM Batch** is a Codex skill for batch adding Chinese subtitles and background music to videos.

It helps you take raw videos or folders of videos and turn them into ready-to-publish clips with burned-in subtitles and mixed BGM.

## What it does

- Batch processes one video, many videos, or an input folder
- Uses Whisper to transcribe Chinese speech
- Burns subtitles into the video
- Mixes the original audio with background music
- Saves transcript JSON sidecars for each video

## Install the skill

Clone or copy the skill into Codex's skills directory:

```bash
git clone https://github.com/ziyeprompttheworld/subtitle-bgm-batch-skill ~/.codex/skills/subtitle-bgm-batch
```

If you already have the files locally, copy them instead:

```bash
cp -R /path/to/subtitle-bgm-batch ~/.codex/skills/subtitle-bgm-batch
```

## Add background music

This repo does not include the large `bgm.mp3` file in Git.

Place your own MP3 here:

```text
~/.codex/skills/subtitle-bgm-batch/assets/bgm.mp3
```

Or pass a custom file at runtime with `--bgm`.

## Requirements

- `ffmpeg`
- `ffprobe`
- Python 3
- `whisper`
- `Pillow`

## Usage

Run the bundled script directly:

```bash
python3 ~/.codex/skills/subtitle-bgm-batch/scripts/add_subtitle_bgm_batch.py \
  --input /path/to/video_or_folder \
  --output /path/to/output_folder
```

Examples:

```bash
# Process a folder
python3 ~/.codex/skills/subtitle-bgm-batch/scripts/add_subtitle_bgm_batch.py \
  --input /Users/ziye/Desktop/视频/CleanShot录屏/待剪辑 \
  --output /Users/ziye/Desktop/视频/CleanShot录屏/已剪辑

# Process multiple files
python3 ~/.codex/skills/subtitle-bgm-batch/scripts/add_subtitle_bgm_batch.py \
  --input video1.mp4 video2.mov \
  --output ./output_subtitle_bgm

# Use a custom BGM file
python3 ~/.codex/skills/subtitle-bgm-batch/scripts/add_subtitle_bgm_batch.py \
  --input ./videos \
  --bgm ./music.mp3
```

## Trigger phrases

Use this skill when you ask for:

- 加字幕
- 加配乐
- 批量输出
- burn subtitles
- add background music
- batch process videos

## Output

- Final video: `<original_stem>_subtitle_bgm.mp4`
- Transcript JSON: `<output>/transcripts/<original_stem>_transcription.json`
