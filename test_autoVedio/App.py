# app.py
import streamlit as st
import threading
import queue
import os
import sys
import time
from datetime import datetime
# ── 页面配置 ────────────────────────────────────────────────
st.set_page_config(
    page_title="AI 短视频生成器",
    page_icon="🎬",
    layout="centered"
)

# ── 样式 ────────────────────────────────────────────────────
st.markdown("""
<style>
.main-title {
    font-size: 2.5rem;
    font-weight: 700;
    text-align: center;
    background: linear-gradient(135deg, #667eea, #764ba2);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.5rem;
}
.sub-title {
    text-align: center;
    color: #666;
    margin-bottom: 2rem;
    font-size: 1rem;
}
.step-box {
    background: #f8f9fa;
    border-left: 4px solid #667eea;
    padding: 0.8rem 1rem;
    margin: 0.4rem 0;
    border-radius: 0 8px 8px 0;
    font-size: 0.9rem;
}
.step-box.done {
    border-left-color: #28a745;
    background: #f0fff4;
}
.step-box.running {
    border-left-color: #ffc107;
    background: #fffdf0;
}
.result-box {
    background: #f0fff4;
    border: 2px solid #28a745;
    border-radius: 12px;
    padding: 1.5rem;
    text-align: center;
    margin-top: 1rem;
}
</style>
""", unsafe_allow_html=True)

# ── 标题 ────────────────────────────────────────────────────
st.markdown('<div class="main-title">🎬 AI 短视频生成器</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">输入主题，自动生成完整短视频</div>', unsafe_allow_html=True)

# ── 流水线步骤定义 ───────────────────────────────────────────
STEPS = [
    ("📝", "script",     "生成脚本"),
    ("🎵", "bgm",        "匹配BGM"),
    ("🎤", "audio",      "合成语音"),
    ("⏱️", "asr",        "提取时间戳"),
    ("🖼️", "images",     "生成配图"),
    ("🎬", "video",      "合成视频"),
    ("✍️", "title_desc", "生成标题描述"),
    ("🖼️", "thumbnail",  "生成封面"),
]

# ── Session State 初始化 ─────────────────────────────────────
if "running"       not in st.session_state: st.session_state.running       = False
if "done"          not in st.session_state: st.session_state.done          = False
if "current_step"  not in st.session_state: st.session_state.current_step  = None
if "completed"     not in st.session_state: st.session_state.completed     = set()
if "result"        not in st.session_state: st.session_state.result        = None
if "error"         not in st.session_state: st.session_state.error         = None
if "log_queue"     not in st.session_state: st.session_state.log_queue     = queue.Queue()
if "logs"          not in st.session_state: st.session_state.logs          = []


# ── 核心：运行 Pipeline ──────────────────────────────────────
def run_pipeline(topic: str, bgm_style: str, log_q: queue.Queue):
    """在子线程里跑完整 pipeline，通过 queue 传递状态"""
    try:
        from transcript_agent import generate_script
        from audio_agent      import generate_audio
        from Asr_agent        import generate_transcript
        from images_agent     import generate_images
        from Video_agent      import create_video_with_overlays
        from title_desc_agent import generate_title_description
        from thumbnail_agent  import generate_thumbnail

        # BGM 映射
        BGM_MAP = {
            "科技感": "assets/bgm_tech.mp3",
            "轻松愉快": "assets/bgm_chill.mp3",
            "励志激昂": "assets/bgm_inspire.mp3",
            "默认":    "assets/bgm_default.mp3",
        }
        bgm_path = BGM_MAP.get(bgm_style, "assets/bgm_default.mp3")

        state = {"topic": topic, "bg_music_path": bgm_path}

        def step(name, fn, s):
            log_q.put(("step", name))
            result = fn(s)
            log_q.put(("done", name))
            return {**s, **result}

        # 逐步执行
        state = step("script",     lambda s: generate_script(s),             state)
        state = step("bgm",        lambda s: {"bg_music_path": bgm_path},    state)
        state = step("audio",      lambda s: generate_audio(s),              state)
        state = step("asr",        lambda s: generate_transcript(s),         state)
        state = step("images",     lambda s: generate_images(s),             state)
        state = step("video",      lambda s: create_video_with_overlays(s),  state)
        state = step("title_desc", lambda s: generate_title_description({
                                        **s, "script": s.get("full_script", "")
                                    }),                                       state)
        state = step("thumbnail",  lambda s: generate_thumbnail(s),          state)

        log_q.put(("result", state))

    except Exception as e:
        log_q.put(("error", str(e)))


# ── 侧边栏配置 ───────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ 生成配置")

    bgm_style = st.selectbox(
        "背景音乐风格",
        ["科技感", "轻松愉快", "励志激昂", "默认"],
        index=3
    )

    st.divider()
    st.caption("📊 流水线步骤")
    for icon, key, label in STEPS:
        if key in st.session_state.completed:
            st.success(f"{icon} {label}", icon="✅")
        elif key == st.session_state.current_step:
            st.warning(f"{icon} {label} ...", icon="⏳")
        else:
            st.caption(f"{icon} {label}")

    if st.session_state.running:
        st.divider()
        if st.button("🛑 取消", use_container_width=True):
            st.session_state.running = False
            st.rerun()


# ── 主界面 ───────────────────────────────────────────────────
col1, col2 = st.columns([4, 1])
with col1:
    topic = st.text_input(
        "输入视频主题",
        placeholder="例如：AI技术发展、量子计算、Mars探索...",
        disabled=st.session_state.running,
        label_visibility="collapsed"
    )
with col2:
    generate_btn = st.button(
        "生成" if not st.session_state.running else "生成中...",
        use_container_width=True,
        disabled=st.session_state.running or not topic,
        type="primary"
    )

# ── 点击生成 ─────────────────────────────────────────────────
if generate_btn and topic and not st.session_state.running:
    # 重置状态
    st.session_state.running      = True
    st.session_state.done         = False
    st.session_state.current_step = None
    st.session_state.completed    = set()
    st.session_state.result       = None
    st.session_state.error        = None
    st.session_state.logs         = []
    st.session_state.log_queue    = queue.Queue()

    # 启动子线程
    t = threading.Thread(
        target=run_pipeline,
        args=(topic, bgm_style, st.session_state.log_queue),
        daemon=True
    )
    t.start()
    st.rerun()


# ── 运行中：轮询队列更新状态 ─────────────────────────────────
if st.session_state.running:
    progress_bar  = st.progress(0)
    status_text   = st.empty()
    log_container = st.container()

    total = len(STEPS)

    # 处理队列消息
    q = st.session_state.log_queue
    while not q.empty():
        msg_type, msg_data = q.get()

        if msg_type == "step":
            st.session_state.current_step = msg_data
            st.session_state.logs.append(f"⏳ 开始：{msg_data}")

        elif msg_type == "done":
            st.session_state.completed.add(msg_data)
            st.session_state.current_step = None
            st.session_state.logs.append(f"✅ 完成：{msg_data}")

        elif msg_type == "result":
            st.session_state.result  = msg_data
            st.session_state.running = False
            st.session_state.done    = True

        elif msg_type == "error":
            st.session_state.error   = msg_data
            st.session_state.running = False

    # 更新进度
    done_count = len(st.session_state.completed)
    progress   = done_count / total
    progress_bar.progress(progress)

    step_labels = {k: label for _, k, label in STEPS}
    cur = st.session_state.current_step
    if cur:
        status_text.info(f"⏳ 正在执行：{step_labels.get(cur, cur)}")
    else:
        status_text.info(f"已完成 {done_count} / {total} 步")

    # 日志
    with log_container:
        with st.expander("📋 执行日志", expanded=True):
            for log in st.session_state.logs[-10:]:
                st.text(log)

    # 自动刷新
    time.sleep(1)
    st.rerun()


# ── 完成：展示结果 ───────────────────────────────────────────
if st.session_state.done and st.session_state.result:
    r = st.session_state.result

    st.success("🎉 视频生成完成！")

    # 视频播放
    video_path = r.get("final_video_path")
    if video_path and os.path.exists(video_path):
        st.video(video_path)
        with open(video_path, "rb") as f:
            st.download_button(
                label="⬇️ 下载视频",
                data=f,
                file_name=f"shorts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
                mime="video/mp4",
                use_container_width=True
            )

    st.divider()

    # 标题 + 描述
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**📌 视频标题**")
        title = r.get("title", "")
        st.code(title)
        st.button("📋 复制标题", on_click=lambda: st.write(title))

    with col_b:
        st.markdown("**📝 视频描述**")
        desc = r.get("description", "")
        st.text_area("", value=desc, height=100, label_visibility="collapsed")

    # 封面图
    thumbnail = r.get("thumbnail_url")
    if thumbnail and os.path.exists(thumbnail):
        st.divider()
        st.markdown("**🖼️ 封面图**")
        col_img, col_dl = st.columns([3, 1])
        with col_img:
            st.image(thumbnail, width=300)
        with col_dl:
            with open(thumbnail, "rb") as f:
                st.download_button(
                    "⬇️ 下载封面",
                    data=f,
                    file_name="thumbnail.jpg",
                    mime="image/jpeg"
                )

    st.divider()
    if st.button("🔄 生成新视频", use_container_width=True, type="primary"):
        st.session_state.done   = False
        st.session_state.result = None
        st.rerun()


# ── 错误展示 ─────────────────────────────────────────────────
if st.session_state.error:
    st.error(f"❌ 生成失败：{st.session_state.error}")
    if st.button("🔄 重试"):
        st.session_state.error   = None
        st.session_state.running = False
        st.rerun()