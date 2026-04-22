from langchain.chat_models import init_chat_model
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser

from langchain_core.prompts import ChatPromptTemplate
import os

tavily = TavilySearchResults(max_results=3
                             ,tavily_api_key="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")(自己去获取)
llm = init_chat_model(
    model="deepseek-chat",
    api_key="sk-d4330db14afa484798cbc3aedd8fd",
    base_url="https://api.deepseek.com"
)

def research_and_generate_transcript(state):
    print("Researching and generating transcript...")
    topic = state["topic"]
    
    # Web research
    # tavily_results = tavily.invoke({"query": topic})

    # print(tavily_results["content"])
    #
    # print(tavily_results)
    
    # Generate script
    script_prompt = ChatPromptTemplate.from_template(
        """为以下主题创作一个吸引人的 30 秒 YouTube Shorts 视频脚本：{topic}
        使用以下研究资料：
        {research}
        请严格遵循以下指南：
        1. 开场钩子（0-5秒）：用一句能立刻抓住观众注意力的开场白开始
        2. 核心内容（5-25秒）：用简短有力的话语呈现关键信息
        3. 行动号召（25-30秒）：以一个吸引人的号召结束，引导观众行动

        每个片段必须满足以下要求：
        - 使用日常对话式的、自然的口语表达风格
        - 使用感叹词，例如“嘿！”、“哇！”、“你绝对想不到！”
        - 加入情感强调（“这太不可思议了！”、“我太激动了，想和大家分享……”）
        - 用“...”来表示自然的停顿，增加戏剧效果
        - 使用反问句来增强与观众的互动
        - 避免任何格式符号或特殊字符
        - 听起来要真实、自然，像真人说话一样
        - JSON 中的 text 字段只能包含纯文本内容

        请严格按照以下 JSON 格式输出（输出内容必须和下面例子完全一致的结构）：
        {{
            "videoScript": [
                {{
                    "start": "00:00",
                    "duration": "00:02",
                    "text": "嘿大家！你们绝对猜不到我发现了什么..."
                }},
                ...
            ],
            "totalDuration": "00:30"
        }}"""
    )

    prompt_filled = script_prompt.invoke({"topic": "AI发展","research":"hahah"})
    llm_output = llm.invoke(prompt_filled)
    print(llm_output.content)
    result = JsonOutputParser().invoke(llm_output)
    print("=============")
    print(result)

    return result

    # chain = script_prompt | llm | JsonOutputParser()
    
    # script = chain.invoke({
    #     "topic": topic,
    #     "research": f"Research: {tavily_results}"
    # })
    # print("Script generated:", script)
    # return {"script": script}

if __name__ == "__main__":
    test_state = {
        "topic": "目前的ai发展的状况！！！"
    }

    result = research_and_generate_transcript(test_state)

    print("\n=== 返回的完整结果 ===")
    print(result)

