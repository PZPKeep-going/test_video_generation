from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
import os

llm = init_chat_model(
    model="deepseek-chat",
    api_key="sk-d4330db14afa484798cbc3aedd8fd702",
    base_url="https://api.deepseek.com"
)

def generate_title_description(state):
    print("Generating title and description...")
    prompt = ChatPromptTemplate.from_template(
        """为以下脚本生成吸引人的 YouTube Shorts 元数据：

        {script}

        请严格遵循以下指南：

        1. 标题（Title）必须满足：
           - 以强有力的动作词或数字开头
           - 包含热门搜索关键词（trending keywords）
           - 制造好奇心或紧迫感
           - 针对 YouTube 搜索进行优化
           - 总长度控制在 60 个字符以内

        2. 描述（Description）必须满足：
           - 以吸引人的钩子开头
           - 包含相关热门标签（hashtags）
           - 适当使用表情符号（emojis）
           - 加入明确的行动号召（Call-to-Action）
           - 总长度控制在 200 个字符以内

        请严格按照以下 JSON 格式返回（输出内容必须和下面例子结构完全一致，不要添加任何额外文字）：
        {{
            "title": "吸引人的标题，控制在60字符以内",
            "description": "吸引人的描述，包含表情符号和行动号召（控制在200字符以内）"
        }}"""
    )
    chain = prompt | llm | JsonOutputParser()
    metadata = chain.invoke({"script": state["script"]})
    print("Metadata generated:", metadata)
    return {"title": metadata["title"], "description": metadata["description"]}
