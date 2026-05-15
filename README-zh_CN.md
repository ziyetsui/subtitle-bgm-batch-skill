# subtitle-bgm-batch-skill

[English](README.md) | **中文**

**Subtitle + BGM Batch** 是一个 Codex skill，用来批量给视频添加中文字幕和背景音乐。

它适合把原始录屏或一组视频，批量处理成带烧录字幕和配乐的可发布版本。

## 功能

- 支持单个视频、多个视频或整个文件夹批量处理
- 使用 Whisper 转录中文语音
- 将字幕直接烧录进视频
- 将原始音频与背景音乐混音
- 为每个视频保留一份转录 JSON

## Skill 安装

将仓库克隆到 Codex 的 skills 目录：

```bash
git clone https://github.com/ziyeprompttheworld/subtitle-bgm-batch-skill ~/.codex/skills/subtitle-bgm-batch
```

如果你已经在本地有文件，也可以直接复制：

```bash
cp -R /path/to/subtitle-bgm-batch ~/.codex/skills/subtitle-bgm-batch
```

## 放置背景音乐

这个仓库没有把 `bgm.mp3` 一起提交到 Git，因为文件太大，超过了 GitHub 普通单文件 100MB 限制。

把你自己的 MP3 放到这里：

```text
~/.codex/skills/subtitle-bgm-batch/assets/bgm.mp3
```

也可以在运行时通过 `--bgm` 指定：

```bash
python3 ~/.codex/skills/subtitle-bgm-batch/scripts/add_subtitle_bgm_batch.py \
  --input /path/to/videos \
  --bgm /path/to/bgm.mp3
```

## 依赖

- `ffmpeg`
- `ffprobe`
- Python 3
- `whisper`
- `Pillow`

## 使用方式

直接运行 skill 自带脚本：

```bash
python3 ~/.codex/skills/subtitle-bgm-batch/scripts/add_subtitle_bgm_batch.py \
  --input /path/to/video_or_folder \
  --output /path/to/output_folder
```

示例：

```bash
# 处理一个文件夹
python3 ~/.codex/skills/subtitle-bgm-batch/scripts/add_subtitle_bgm_batch.py \
  --input /Users/ziye/Desktop/视频/CleanShot录屏/待剪辑 \
  --output /Users/ziye/Desktop/视频/CleanShot录屏/已剪辑

# 处理多个视频
python3 ~/.codex/skills/subtitle-bgm-batch/scripts/add_subtitle_bgm_batch.py \
  --input video1.mp4 video2.mov \
  --output ./output_subtitle_bgm

# 自定义 BGM
python3 ~/.codex/skills/subtitle-bgm-batch/scripts/add_subtitle_bgm_batch.py \
  --input ./videos \
  --bgm ./music.mp3
```

## 触发词

以下需求适合触发这个 skill：

- 加字幕
- 加配乐
- 批量输出
- burn subtitles
- add background music
- batch process videos

## 输出结果

- 成品视频：`<原文件名>_subtitle_bgm.mp4`
- 转录 JSON：`<output>/transcripts/<原文件名>_transcription.json`
