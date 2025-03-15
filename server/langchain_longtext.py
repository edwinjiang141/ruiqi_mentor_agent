from langchain.chains import TransformChain, LLMChain, SimpleSequentialChain
from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence
from langchain.llms import Ollama
with open("./the_old_man_and_the_sea.txt", encoding='utf-8') as f:
    novel_text = f.read()

# 定义一个转换函数，输入是一个字典，输出也是一个字典。
def transform_func(inputs: dict) -> dict:
    # 从输入字典中获取"text"键对应的文本。
    text = inputs["text"]
    # 使用split方法将文本按照"\n\n"分隔为多个段落，并只取前三个，然后再使用"\n\n"将其连接起来。
    shortened_text = "\n\n".join(text.split("\n\n")[:3])
    # 返回裁剪后的文本，用"output_text"作为键。
    return {"output_text": shortened_text}

# 使用上述转换函数创建一个TransformChain对象。
# 定义输入变量为["text"]，输出变量为["output_text"]，并指定转换函数为transform_func。
transform_chain = TransformChain(
    input_variables=["text"], output_variables=["output_text"], transform=transform_func
)

transformed_novel = transform_chain.invoke(novel_text)
template = """总结下面文本:

{output_text}

总结:"""

ollama_llm = Ollama(model="deepseek-r1:32b")
prompt = PromptTemplate(input_variables=["output_text"], template=template)
llm_chain = LLMChain(llm=ollama_llm, prompt=prompt, verbose=True)
sequential_chain = SimpleSequentialChain(chains=[transform_chain, llm_chain])
print(sequential_chain.invoke(novel_text[:100]))