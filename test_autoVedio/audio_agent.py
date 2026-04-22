# audio_agent.py
import os
import dashscope
from datetime import datetime
from typing import Dict

dashscope.api_key = "sk-9b051438df8d4d1b95df94e6a55baef1"

def generate_audio(state: Dict) -> Dict:
    """
    Audio Agent: 将上一个 Agent 生成的 full_script 转为语音音频
    输入: state 中必须包含 "full_script"
    输出: 在 state 中新增 "audio_path"
    """
    print("🎤 Audio Agent: 正在生成语音...")

    # 从 state 中获取脚本文字
    text = state.get("full_script")
    if not text:
        raise ValueError("Error in audio_agent: 'full_script' not found in state")

    try:
        from dashscope.audio.tts_v2 import SpeechSynthesizer

        # 创建合成器
        synthesizer = SpeechSynthesizer(
            model='cosyvoice-v3-flash',
            voice='longanyang',        # 你目前使用的音色
            # 可根据需要调整参数：
            # format='mp3',
            # rate=1.0,                # 语速
            # pitch=1.0,               # 音调
            # volume=50,
        )

        # 生成音频
        audio_data = synthesizer.call(text)

        # 保存音频文件
        os.makedirs("output/audios", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_path = f"output/audios/audio_{timestamp}.mp3"

        with open(audio_path, 'wb') as f:
            f.write(audio_data)

        print(f"✅ Audio generated successfully: {audio_path}")
        print(f"音频长度: {len(audio_data) / 1024:.2f} KB")

        # 返回更新后的 state
        return {
            **state,                    # 保留之前的所有内容
            "audio_path": audio_path
        }

    except Exception as e:
        print(f"❌ Audio Agent failed: {str(e)}")
        if "API key" in str(e).lower():
            print("提示: 请检查 DashScope API Key 是否有效")
        # 返回错误信息，方便 LangGraph 处理
        return {
            **state,
            "error": f"Audio generation failed: {str(e)}"
        }


# ====================== 测试 ======================
if __name__ == "__main__":
    # 测试用的 state（模拟上一个 agent 的输出）
    test_state = {
        "topic": "目前的AI发展状况",
        "full_script": "嘿大家！AI发展真的太快了，你绝对猜不到接下来会发生什么... 这简直太不可思议了！我太激动了，必须和大家分享这个时代浪潮！"
    }

    result = generate_audio(test_state)
    print("\n=== 返回结果 ===")
    print(result)