AI 短视频自动生成系统（test_autoVedio）
========================================
一、项目做什么
------------
输入一个“主题”，自动完成：
1) 检索增强生成口播脚本（LLM + Tavily）
2) TTS 合成配音（DashScope）
3) Whisper ASR 转写，得到带时间戳的字幕分段（videoScript）
4) 按分段生成配图（DashScope 多模态图像）
5) MoviePy 合成 9:16 竖版短视频（配图 + 字幕 + 配音 + BGM）
6) 生成标题/描述与封面图
主要入口：
- App.py：Streamlit Web 界面
- mian.py：LangGraph 工作流命令行入口
二、如何启动
------------
1) 启动 Web 界面（推荐）
   streamlit run App.py
2) 直接跑命令行流水线
   python mian.py
三、项目用到的依赖（来自你提供的 pip list）
--------------------------------------
下面这些是本项目源码中实际 import/调用到的依赖包及版本：
- streamlit==1.56.0
  用途：提供可视化页面（App.py）
- langgraph==1.1.4
  用途：工作流编排（mian.py）
- langchain==1.2.14
- langchain-core==1.2.26
- langchain-community==0.4.1
  用途：LLM 调用与 Tavily 工具封装（transcript_agent.py / images_agent.py / title_desc_agent.py）
- tavily-python==0.7.23
  用途：主题检索增强（transcript_agent.py）
- dashscope==1.25.16
  用途：TTS（audio_agent.py）与图像生成（images_agent.py / thumbnail_agent.py）
- openai-whisper==20250625
  用途：ASR 转写与分段时间戳（Asr_agent.py）
- moviepy==2.2.1
  用途：视频合成（Video_agent.py）
- numpy==2.2.6
  用途：背景音乐拼接/循环等计算（Video_agent.py）
- requests==2.32.5
  用途：下载生成的图片等（images_agent.py / thumbnail_agent.py）
- imageio-ffmpeg==0.6.0
  用途：提供 ffmpeg 可执行文件路径（Asr_agent.py）
四、运行前准备（重要）
-------------------
1) API Key（建议用环境变量管理，不要硬编码进仓库）
   - Tavily API Key：用于检索增强
   - DeepSeek API Key：用于脚本/提示词/标题描述生成（LLM）
   - DashScope API Key：用于 TTS 与图像生成
2) ffmpeg
   - 本项目在 Asr_agent.py 中使用 imageio-ffmpeg 获取 ffmpeg 路径并尝试复制 ffmpeg.exe
   - 仍建议确保本机可用 ffmpeg（避免路径/权限问题）
3) Python 版本
   - 建议使用和你当前环境一致的 Python 版本运行（以避免依赖兼容问题）
五、输出目录
