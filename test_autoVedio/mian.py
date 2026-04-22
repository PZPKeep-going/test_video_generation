# # main.py
# from typing import TypedDict, List, Optional
# from langgraph.graph import END, StateGraph
#
# from transcript_agent import generate_script
# from audio_agent import generate_audio
# from Asr_agent import generate_transcript
# from images_agent import generate_images
# from Video_agent import create_video_with_overlays
#
#
# # ── 1. State 定义 ────────────────────────────────────────────
# class AgentState(TypedDict):
#     # 输入
#     topic: str
#
#     # transcript_agent 输出
#     full_script: Optional[str]
#
#     # audio_agent 输出
#     audio_path: Optional[str]
#
#     # asr_agent 输出
#     videoScript: Optional[dict]
#     raw_transcript: Optional[str]
#
#     # images_agent 输出
#     images_manifest: Optional[List[dict]]
#
#     # video_agent 输出（如果有头像视频）
#     avatar_video_path: Optional[str]
#     final_video_path: Optional[str]
#
#     # 可选：背景音乐
#     bg_music_path: Optional[str]
#
#     # 错误信息
#     error: Optional[str]
#
#
# # ── 2. 节点函数 ──────────────────────────────────────────────
# def node_transcript(state: AgentState) -> dict:
#     """生成文字脚本"""
#     result = generate_script(state)
#     return {"full_script": result["full_script"]}
#
#
# def node_audio(state: AgentState) -> dict:
#     """文字 → 音频"""
#     result = generate_audio(state)
#     return {"audio_path": result["audio_path"]}
#
#
# def node_asr(state: AgentState) -> dict:
#     """音频 → 带时间戳文字（Whisper）"""
#     result = generate_transcript(state)
#     return {
#         "videoScript":      result.get("videoScript"),
#         "raw_transcript":   result.get("raw_transcript"),
#     }
#
#
# def node_images(state: AgentState) -> dict:
#     """每段文字 → AI 生成配图"""
#     result = generate_images(state)
#     return {"images_manifest": result["images_manifest"]}
#
#
# def node_video(state: AgentState) -> dict:
#     """合成最终视频（图片 + 字幕 + 音频）"""
#     # 如果没有 avatar 视频，用音频直接合成（需要 video_agent 支持纯音频模式）
#     result = create_video_with_overlays(state)
#     return {"final_video_path": result["final_video_path"]}
#
#
# # ── 3. 构建工作流 ─────────────────────────────────────────────
# def build_workflow() -> StateGraph:
#     workflow = StateGraph(AgentState)
#
#     # 注册节点
#     workflow.add_node("transcript_agent", node_transcript)
#     workflow.add_node("audio_agent",      node_audio)
#     workflow.add_node("asr_agent",        node_asr)
#     workflow.add_node("images_agent",     node_images)
#     workflow.add_node("video_agent",      node_video)
#
#     # 设置入口
#     workflow.set_entry_point("transcript_agent")
#
#     # 串行流水线
#     workflow.add_edge("transcript_agent", "audio_agent")
#     workflow.add_edge("audio_agent",      "asr_agent")
#     workflow.add_edge("asr_agent",        "images_agent")
#     workflow.add_edge("images_agent",     "video_agent")
#     workflow.add_edge("video_agent",      END)
#
#     return workflow.compile()
#
#
# # ── 4. 运行 ──────────────────────────────────────────────────
# if __name__ == "__main__":
#     app = build_workflow()
#
#     init_state = {
#         "topic":          "目前的AI发展状况",
#         # 如果有头像视频，填入路径；没有则 video_agent 用图片+音频合成
#         # "avatar_video_path": "output/avatar/xxx.mp4",
#     }
#
#     print("🚀 开始运行 AI 视频生成 Pipeline...")
#     print(f"📌 主题: {init_state['topic']}")
#     print("=" * 50)
#
#     result = app.invoke(init_state)
#
#     print("\n" + "=" * 50)
#     print("🎉 Pipeline 完成！")
#     print(f"📹 最终视频: {result.get('final_video_path', '未生成')}")
#     if result.get("error"):
#         print(f"⚠️  错误信息: {result['error']}")

# main.py
from typing import TypedDict, List, Optional
from langgraph.graph import END, StateGraph

from transcript_agent import generate_script
from audio_agent import generate_audio
from Asr_agent import generate_transcript
from images_agent import generate_images
from Video_agent import create_video_with_overlays
from title_desc_agent import generate_title_description
from thumbnail_agent import generate_thumbnail


# ── 1. State 定义 ────────────────────────────────────────────
class AgentState(TypedDict):
    topic:           str

    # transcript_agent
    full_script:     Optional[str]

    # audio_agent
    audio_path:      Optional[str]

    # asr_agent
    videoScript:     Optional[dict]
    raw_transcript:  Optional[str]

    # images_agent
    images_manifest: Optional[List[dict]]

    # video_agent
    final_video_path: Optional[str]

    # title_desc_agent
    title:           Optional[str]
    description:     Optional[str]

    # thumbnail_agent
    thumbnail_url:   Optional[str]

    # 可选
    bg_music_path:   Optional[str]
    error:           Optional[str]


# ── 2. 节点函数 ──────────────────────────────────────────────
def node_transcript(state: AgentState) -> dict:
    result = generate_script(state)
    return {"full_script": result["full_script"]}


def node_audio(state: AgentState) -> dict:
    result = generate_audio(state)
    return {"audio_path": result["audio_path"]}


def node_asr(state: AgentState) -> dict:
    result = generate_transcript(state)
    return {
        "videoScript":    result.get("videoScript"),
        "raw_transcript": result.get("raw_transcript"),
    }


def node_images(state: AgentState) -> dict:
    result = generate_images(state)
    return {"images_manifest": result["images_manifest"]}


def node_video(state: AgentState) -> dict:
    result = create_video_with_overlays(state)
    return {"final_video_path": result["final_video_path"]}


def node_title_desc(state: AgentState) -> dict:
    """用 full_script 生成标题和描述"""
    # title_desc_agent 原来用 state["script"]，
    # 现在我们把 full_script 映射过去
    result = generate_title_description({
        **state,
        "script": state.get("full_script", "")
    })
    return {
        "title":       result["title"],
        "description": result["description"],
    }


def node_thumbnail(state: AgentState) -> dict:
    """用 title + description 生成封面图"""
    result = generate_thumbnail(state)
    return {"thumbnail_url": result["thumbnail_url"]}


# ── 3. 构建工作流 ─────────────────────────────────────────────
def build_workflow():
    workflow = StateGraph(AgentState)

    workflow.add_node("transcript_agent", node_transcript)
    workflow.add_node("audio_agent",      node_audio)
    workflow.add_node("asr_agent",        node_asr)
    workflow.add_node("images_agent",     node_images)
    workflow.add_node("video_agent",      node_video)
    workflow.add_node("title_desc_agent", node_title_desc)
    workflow.add_node("thumbnail_agent",  node_thumbnail)

    workflow.set_entry_point("transcript_agent")

    workflow.add_edge("transcript_agent", "audio_agent")
    workflow.add_edge("audio_agent",      "asr_agent")
    workflow.add_edge("asr_agent",        "images_agent")
    workflow.add_edge("images_agent",     "video_agent")

    # 视频生成完后，串行生成标题→封面
    workflow.add_edge("video_agent",      "title_desc_agent")
    workflow.add_edge("title_desc_agent", "thumbnail_agent")
    workflow.add_edge("thumbnail_agent",  END)

    return workflow.compile()


# ── 4. 运行 ──────────────────────────────────────────────────
if __name__ == "__main__":
    app = build_workflow()

    result = app.invoke({
        "topic":         "目前的手机发展状况",
        # "bg_music_path": "assets/bg_music.mp3",
    })

    print("\n" + "=" * 50)
    print("🎉 Pipeline 完成！")
    print(f"📹 视频:  {result.get('final_video_path')}")
    print(f"📌 标题:  {result.get('title')}")
    print(f"📝 描述:  {result.get('description')}")
    print(f"🖼️  封面:  {result.get('thumbnail_url')}")