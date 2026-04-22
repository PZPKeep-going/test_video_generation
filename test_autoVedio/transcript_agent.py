# from langchain.chat_models import init_chat_model
# from langchain_community.tools.tavily_search import TavilySearchResults
# from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
#
# from langchain_core.prompts import ChatPromptTemplate
# import os
#
# tavily = TavilySearchResults(max_results=3
#                              ,tavily_api_key="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")
# llm = init_chat_model(
#     model="deepseek-chat",
#     api_key="sk-d4330db14afa484798cbc3aedd8fd702",
#     base_url="https://api.deepseek.com"
# )
# def research_and_generate_transcript(state):
#     print("Researching and generating transcript...")
#     topic = state["topic"]
#
#     # Web research
#     tavily_results = tavily.invoke({"query": topic})
#
#     # print(tavily_results["content"])
#     #
#     print(tavily_results)
#
#     # Generate script
#     script_prompt = ChatPromptTemplate.from_template(
#         """为以下主题创作一个吸引人的 30 秒 B站/抖音 视频脚本：{topic}
#         使用以下研究资料：
#         {research}
#         每个片段必须满足以下要求：
#         - 使用自然、口语化的表达，像真人说话一样
#         - 开场要有强有力的钩子
#         - 加入感叹词、反问句、停顿（...）
#         - 用“...”来表示自然的停顿，增加戏剧效果
#         - 情绪饱满，适合短视频
#         - 总时长控制在30秒左右
#         请直接返回一段连贯的文字脚本，不要带任何时间戳"""
#     )
#     prompt_filled = script_prompt.invoke({"topic": topic,"research":tavily_results})
#     llm_output = llm.invoke(prompt_filled)
#
#     script = StrOutputParser().invoke(llm_output)
#
#     print("Script generated:",script)
#
#     return {"script":script}
#
#
#
# if __name__ == "__main__":
#     test_state = {
#         "topic": "目前的家电的发展的状况！！！"
#     }
#
#     result = research_and_generate_transcript(test_state)
#
#     print("\n=== 返回的完整结果 ===")
#     print(result)

from langchain.chat_models import init_chat_model
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

tavily = TavilySearchResults(max_results=3, tavily_api_key="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")

llm = init_chat_model(
    model="deepseek-chat",
    api_key="sk-d4330db14afa484798cbc3aedd8fd702",
    base_url="https://api.deepseek.com"
)

def generate_script(state):
    """生成短视频纯文字脚本（推荐的新函数名）"""
    print("📝 Generating script...")

    topic = state["topic"]

    # 1. 执行搜索
    tavily_results = tavily.invoke(topic)

    # 2. 提取有用的研究内容（只取 content 部分）
    research_text = "\n\n".join([
        f"资料{i+1}：{result.get('content', '')[:600]}"
        for i, result in enumerate(tavily_results)
    ])

    # 3. 优化后的 Prompt
    script_prompt = ChatPromptTemplate.from_template(
        """你是一个专业的短视频脚本作家。请为以下主题创作一个**自然、口语化、适合真人直接念**的 30 秒抖音/B站短视频脚本。

主题：{topic}

参考资料：
{research}

写作要求：
- 使用非常日常、自然的口语，像和朋友聊天一样
- 开场要强有力，能立刻抓住观众注意力（可以用“嘿！”、“你知道吗？”、“太离谱了！”等）
- 多使用感叹号、反问句、自然停顿（...）
- 情绪要饱满，节奏要有起伏
- 总长度控制在 130-160 字左右（适合30秒左右）
- **禁止**出现任何镜头描述、括号说明、画面提示（如（镜头切换））

请直接返回一段连贯的纯文字脚本，不要加任何标题、不要输出JSON、不要加额外说明。"""
    )

    chain = script_prompt | llm | StrOutputParser()

    full_script = chain.invoke({
        "topic": topic,
        "research": research_text if research_text else "无外部资料，请基于常识创作。"
    })

    print("✅ Script generated successfully:")
    print("-" * 50)
    print(full_script)
    print("-" * 50)

    return {"full_script": full_script}   # 推荐使用 full_script

# ====================== 测试 ======================
if __name__ == "__main__":
    test_state = {"topic": "目前的家电的发展状况"}
    result = generate_script(test_state)
