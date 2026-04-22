# images_agent.py
import os
import requests
from datetime import datetime
from typing import Dict
import dashscope
from dashscope import MultiModalConversation
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

dashscope.api_key = "sk-9b051438df8d4d1b95df94e6a55baef1"

llm = init_chat_model(
    model="deepseek-chat",
    api_key="sk-d4330db14afa484798cbc3aedd8fd702",
    base_url="https://api.deepseek.com"
)

# ── 提示词生成链 ──────────────────────────────────────────
prompt_chain = ChatPromptTemplate.from_template(
    """你是一个专业的 AI 绘画提示词专家。
根据以下视频片段文字和主题，生成一段用于 AI 文生图的中文提示词。

要求：
1. 画面内容与文字语义高度相关
2. 竖版构图（9:16），适合短视频封面
3. 风格：写实或高质量插画，电影级光影
4. 不超过80字，直接返回提示词，不要任何解释

视频主题：{topic}
片段文字：{text}"""
) | llm | StrOutputParser()


def generate_image(prompt: str, save_path: str) -> bool:
    """调用 Qwen-Image-2.0 生成图片并保存"""
    try:
        response = MultiModalConversation.call(
            model="qwen-image-2.0",
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            result_format="message",
            stream=False,
            watermark=False,
            prompt_extend=True,
            size="1024*1536",   # 竖版
            n=1
        )

        if response.status_code != 200:
            print(f"  ❌ 生成失败: {response.status_code}")
            return False

        image_url = response.output.choices[0].message.content[0]["image"]
        img_data = requests.get(image_url, timeout=30).content
        with open(save_path, "wb") as f:
            f.write(img_data)

        print(f"  ✅ 图片已保存: {save_path}")
        return True

    except Exception as e:
        print(f"  ❌ 图片生成异常: {e}")
        return False


def generate_images(state: Dict) -> Dict:
    """
    Images Agent：为每个视频片段生成配图
    输入: state 包含 videoScript 和 topic
    输出: state 新增 images_manifest
    """
    print("🖼️  Images Agent: 开始生成配图...")

    video_script = state.get("videoScript", {}).get("videoScript", [])
    topic = state.get("topic", "")

    if not video_script:
        raise ValueError("❌ videoScript 为空，请先运行 asr_agent")

    os.makedirs("output/images", exist_ok=True)

    images_manifest = []

    for i, seg in enumerate(video_script):
        text = seg.get("text", "").strip()
        start = seg.get("start", "00:00")
        duration = seg.get("duration", "00:04")

        print(f"\n📌 片段 {i+1}/{len(video_script)}: [{start}] {text[:30]}...")

        # 1. 生成图片提示词
        try:
            image_prompt = prompt_chain.invoke({"topic": topic, "text": text})
            image_prompt = image_prompt.strip()
            print(f"  🎨 提示词: {image_prompt[:60]}...")
        except Exception as e:
            print(f"  ⚠️ 提示词生成失败，使用默认: {e}")
            image_prompt = f"{topic}，{text[:20]}，高质量，竖版构图"

        # 2. 生成图片
        save_path = f"output/images/segment_{i+1:03d}.jpg"
        success = generate_image(image_prompt, save_path)

        # 3. 记录 manifest
        images_manifest.append({
            "start":    start,
            "duration": duration,
            "text":     text,
            "url":      save_path if success else "output/images/placeholder.jpg",
            "prompt":   image_prompt,
        })

    print(f"\n✅ 配图完成！共 {len(images_manifest)} 张")

    return {
        **state,
        "images_manifest": images_manifest,
    }


# ====================== 测试 ======================
if __name__ == "__main__":
    # 模拟 asr_agent 输出的 state
    test_state = {
        "topic": "目前的AI发展状况",
        "videoScript": {
            "videoScript": [
                {"start": "00:00", "duration": "00:05", "text": "人工智能正在以前所未有的速度改变我们的世界"},
                {"start": "00:05", "duration": "00:04", "text": "从医疗到教育，AI的应用已经无处不在"},
                {"start": "00:09", "duration": "00:05", "text": "未来十年，AI将创造出我们无法想象的可能性"},
            ],
            "totalDuration": "00:14"
        }
    }

    result = generate_images(test_state)

    print("\n=== images_manifest ===")
    for item in result["images_manifest"]:
        print(f"[{item['start']}] {item['url']} | {item['text'][:20]}")