# thumbnail_agent.py 改造版（用你已有的 DashScope）
from dashscope import MultiModalConversation
import requests, os, dashscope

dashscope.api_key = "sk-9b051438df8d4d1b95df94e6a55baef1"

def generate_thumbnail(state):
    print("🖼️ 生成封面图...")

    prompt = f"""为视频《{state['title']}》生成封面图。
{state['description']}
要求：竖版构图9:16，视觉冲击力强，色彩鲜艳，电影级光影，适合短视频封面"""

    response = MultiModalConversation.call(
        model="qwen-image-2.0",
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        result_format="message",
        watermark=False,
        prompt_extend=True,
        size="1024*1536",
        n=1
    )

    image_url = response.output.choices[0].message.content[0]["image"]

    os.makedirs("output/thumbnails", exist_ok=True)
    save_path = "output/thumbnails/thumbnail.jpg"
    with open(save_path, "wb") as f:
        f.write(requests.get(image_url, timeout=30).content)

    print(f"✅ 封面已保存: {save_path}")
    return {"thumbnail_url": save_path}