# asr_agent.py
import os
import imageio_ffmpeg
import shutil
import whisper
from typing import Dict

# 确保 ffmpeg 可用
_ffmpeg_src = imageio_ffmpeg.get_ffmpeg_exe()
_ffmpeg_dst = os.path.join(os.path.dirname(_ffmpeg_src).replace("imageio_ffmpeg\\binaries", ""),
                            "..", "..", "Scripts", "ffmpeg.exe")
_ffmpeg_dst = os.path.normpath(_ffmpeg_dst)
if not os.path.exists(_ffmpeg_dst):
    shutil.copy(_ffmpeg_src, _ffmpeg_dst)


def generate_transcript(state: Dict) -> Dict:
    """
    ASR Agent: 使用 Whisper 把音频转成文字（带时间戳）
    输入: state 中必须包含 "audio_path"
    输出: 在 state 中新增 "videoScript"（带时间戳的结构）
    """
    print("🎤 ASR Agent: 正在进行语音转文字...")

    audio_path = state.get("audio_path")
    if not audio_path or not os.path.exists(audio_path):
        raise ValueError(f"Error: audio_path 不存在或文件未找到 → {audio_path}")

    try:
        # 加载模型（首次会下载，后续缓存）
        model = whisper.load_model("base", device="cpu")

        result = model.transcribe(
            audio_path,
            language="zh",
            fp16=False,
            verbose=False,
        )

        segments = result["segments"]
        result_text = result["text"].strip()

        print("✅ Whisper 识别成功！")
        print(f"识别文本长度: {len(result_text)} 字符")
        print(f"识别结果预览: {result_text[:200]}")

        # 构建带时间戳的 videoScript 结构
        def fmt(seconds: float) -> str:
            m, s = divmod(int(seconds), 60)
            return f"{m:02}:{s:02}"

        video_script = {
            "videoScript": [
                {
                    "start": fmt(seg["start"]),
                    "end": fmt(seg["end"]),
                    "duration": round(seg["end"] - seg["start"], 2),
                    "text": seg["text"].strip()
                }
                for seg in segments
            ],
            "totalDuration": fmt(segments[-1]["end"]) if segments else "00:00"
        }

        return {
            **state,
            "raw_transcript": result_text,
            "videoScript": video_script,
        }

    except Exception as e:
        print(f"❌ ASR Agent 执行失败: {str(e)}")
        return {
            **state,
            "error": f"ASR failed: {str(e)}"
        }


# ====================== 测试 ======================
if __name__ == "__main__":
    test_state = {
        "topic": "目前的AI发展状况",
        "full_script": "嘿大家！AI发展真的太快了...",
        "audio_path": "test_audio_20260410_162915.mp3"
    }

    result = generate_transcript(test_state)

    print("\n=== videoScript 结构 ===")
    for seg in result["videoScript"]["videoScript"]:
        print(f"[{seg['start']} → {seg['end']}] {seg['text']}")

    print(f"\n总时长: {result['videoScript']['totalDuration']}")