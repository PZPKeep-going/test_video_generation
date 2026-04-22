# video_agent.py
import os
import numpy as np
from datetime import datetime
from typing import Dict

from moviepy import (
    ImageClip, AudioFileClip, TextClip,
    CompositeVideoClip, ColorClip, concatenate_audioclips, CompositeAudioClip
)

# ── 工具函数 ────────────────────────────────────────────────
def timestamp_to_seconds(ts) -> float:
    if isinstance(ts, (int, float)):
        return float(ts)
    parts = str(ts).split(":")
    if len(parts) == 2:
        return float(parts[0]) * 60 + float(parts[1])
    elif len(parts) == 3:
        return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    return float(ts)


def get_font() -> str:
    candidates = [
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
        r"C:\Windows\Fonts\simsun.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    ]
    for f in candidates:
        if os.path.exists(f):
            return f
    return "Arial"

# ── 字幕片段 ────────────────────────────────────────────────
def make_subtitle_clips(video_script, sw, sh, font):
    clips = []
    for seg in video_script:
        text = seg.get("text", "").strip()
        if not text:
            continue

        start = timestamp_to_seconds(seg.get("start", 0))

        # 兼容 Whisper 输出的 float duration 和 MM:SS 格式
        raw_dur = seg.get("duration")
        if isinstance(raw_dur, float):
            duration = raw_dur
        elif raw_dur is not None:
            duration = timestamp_to_seconds(raw_dur)
        else:
            end = timestamp_to_seconds(seg.get("end", start + 3))
            duration = end - start

        if duration <= 0:
            continue

        try:
            txt = TextClip(
                text=text,
                font=font,
                font_size=52,
                color="white",
                method="caption",
                size=(sw - 80, None),
                text_align="center",
            )

            bg = ColorClip(
                size=(txt.w + 40, txt.h + 24),
                color=(0, 0, 0)
            ).with_opacity(0.6).with_duration(duration)

            subtitle = CompositeVideoClip([
                bg,
                txt.with_position("center")
            ])

            bottom_y = sh - subtitle.h - 120
            subtitle = (subtitle
                        .with_start(start)
                        .with_duration(duration)
                        .with_position(("center", bottom_y)))
            clips.append(subtitle)
        except Exception as e:
            print(f"  ⚠️ 字幕生成失败: {e}")

    return clips

# ── 图片覆盖层 ───────────────────────────────────────────────
def make_image_clips(images_manifest, sw, sh):
    clips = []
    text_reserve = 260

    for seg in images_manifest:
        url = seg.get("url", "")
        if not url or not os.path.exists(url):
            continue

        start = timestamp_to_seconds(seg.get("start", 0))
        raw_dur = seg.get("duration")
        if isinstance(raw_dur, float):
            duration = raw_dur
        else:
            duration = timestamp_to_seconds(raw_dur or 4)

        try:
            img = ImageClip(url)
            available_h = sh - text_reserve
            scale = min(sw / img.w, available_h / img.h)
            img = img.resized(scale)
            x = (sw - img.w) / 2

            img = (img
                   .with_start(start)
                   .with_duration(duration)
                   .with_position((x, 0)))
            clips.append(img)
        except Exception as e:
            print(f"  ⚠️ 图片加载失败 {url}: {e}")

    return clips

# ── 主函数（纯图片+音频模式）────────────────────────────────
def create_video_with_overlays(state: Dict) -> Dict:
    print("🎬 Video Agent: 开始合成视频（纯图片+音频模式）...")

    audio_path      = state.get("audio_path")
    video_script    = state.get("videoScript", {}).get("videoScript", [])
    images_manifest = state.get("images_manifest", [])
    bg_music_path   = state.get("bg_music_path", "assets/bg_music.mp3")

    # ── 必要检查 ──
    if not audio_path or not os.path.exists(audio_path):
        raise ValueError(f"❌ audio_path 不存在: {audio_path}")
    if not video_script:
        raise ValueError("❌ videoScript 为空")

    sw, sh = 1080, 1920

    # 加载音频，获取时长
    main_audio = AudioFileClip(audio_path)
    duration   = main_audio.duration
    print(f"  ⏱️  音频时长: {duration:.2f}s")

    # 背景
    bg = ColorClip(size=(sw, sh), color=(0, 0, 0)).with_duration(duration)

    font = get_font()
    print(f"  🔤 使用字体: {font}")

    # 图片层
    image_clips = make_image_clips(images_manifest, sw, sh)
    print(f"  🖼️  图片片段: {len(image_clips)} 张")

    # 字幕层
    subtitle_clips = make_subtitle_clips(video_script, sw, sh, font)
    print(f"  📝 字幕片段: {len(subtitle_clips)} 条")

    # 背景音乐
    final_audio = main_audio
    if bg_music_path and os.path.exists(bg_music_path):
        try:
            bg_music = AudioFileClip(bg_music_path).with_volume_scaled(0.08)
            if bg_music.duration < duration:
                loops = int(np.ceil(duration / bg_music.duration))
                bg_music = concatenate_audioclips([bg_music] * loops)
            bg_music = bg_music.subclipped(0, duration)
            final_audio = CompositeAudioClip([main_audio, bg_music])
            print(f"  🎵 背景音乐: {bg_music_path}")
        except Exception as e:
            print(f"  ⚠️ 背景音乐失败: {e}")
    else:
        print("  ℹ️  无背景音乐")

    # 合成：背景 → 图片 → 字幕（字幕在最上层）
    all_clips = [bg] + image_clips + subtitle_clips
    composite = (CompositeVideoClip(all_clips, size=(sw, sh))
                 .with_duration(duration)
                 .with_audio(final_audio))

    # 输出
    os.makedirs("output/final_videos", exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"output/final_videos/shorts_{ts}.mp4"

    composite.write_videofile(
        output_path,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        threads=4,
        logger="bar",
    )
    main_audio.close()
    print(f"✅ 视频合成完成: {output_path}")
    return {"final_video_path": output_path}


# ====================== 测试 ======================
if __name__ == "__main__":
    test_state = {
        "audio_path": "output/audios/audio_20260411_155312.mp3",
        "videoScript": {
            "videoScript": [
                {"start": "00:00", "duration": 5.2, "text": "人工智能正在以前所未有的速度改变世界"},
                {"start": "00:05", "duration": 4.1, "text": "从医疗到教育，AI应用已无处不在"},
            ],
            "totalDuration": "00:09"
        },
        "images_manifest": [
            {"start": "00:00", "duration": 5.2, "url": "output/images/segment_001.jpg"},
            {"start": "00:05", "duration": 4.1, "url": "output/images/segment_002.jpg"},
        ],
    }
    result = create_video_with_overlays(test_state)
    print(f"\n🎉 输出路径: {result['final_video_path']}")