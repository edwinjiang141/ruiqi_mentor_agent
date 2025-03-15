from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.vectorstores import FAISS
import os
from langchain_community.chat_models import ChatOllama
from langchain.chains import RetrievalQA
from langchain_ollama.chat_models import ChatOllama 
from langchain_core.tools import tool
from typing import Annotated, Literal
from langchain_core.messages import AIMessage
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI
from typing_extensions import TypedDict
from langgraph.graph import END, StateGraph, START
from langgraph.graph.message import AnyMessage, add_messages
@tool
def query_rag(query:any) -> any:
    """
    RAG query
    """
    enbeddings = OpenAIEmbeddings(openai_api_key = os.environ["OPENAI_API_KEY"],openai_api_base = "https://pro.aiskt.com/v1")
    #当向量数据库中没有合适答案时，使用大语言模型能力

    prompt_template = """ <指令>根据知识库已知的信息，一切生成的内容必须都是知识库里的内容，不允许在答案中添加编造成分，
                        一切生成的内容必须都是知识库里的内容，不允许在答案中添加编造成分，答案请使用中文。 </指令>
                        <已知信息>{context}</已知信息>
                        <问题>{question}</问题> 
                        """

    prompt = PromptTemplate(template = prompt_template,input_variables=["context", "question"])

    document_search = FAISS.load_local("ora_doc_index", enbeddings,allow_dangerous_deserialization = True)

    #llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0,openai_organization = "org-cODSJjftWgVspplR3MwUi2HN",openai_api_key = os.environ["OPENAI_API_KEY"])
    llm = ChatOllama(model="deepseek-r1:32b",max_tokens=8192, temperature=0.8)
    #llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0,openai_api_key = os.environ["OPENAI_API_KEY"],openai_api_base = "https://pro.aiskt.com/v1")
    qa_chain = RetrievalQA.from_llm(llm,
                                retriever=document_search.as_retriever(search_type="similarity_score_threshold",
                                                            search_kwargs={"score_threshold": 0.3}),prompt=prompt)
    # qa_chain.combine_documents_chain.document_prompt = PromptTemplate(input_variables=["query"],template="{page_content}")
    qa_chain.return_source_documents=True
    result = qa_chain({"query": "如何判断数据变化率是否大于阈值"})
    return result['result']


@tool
def summary_rag(summary:any) -> any:
    """
    RAG summary
    """
    summary_prompt = """
                        根据给出的结论进行总结，要求只把关键步骤列出来
                     """
    llm = summary_prompt | ChatOllama(model="deepseek-r1:32b",max_tokens=8192, temperature=0.8)
    return llm.invoke(summary)


# 定义一个新的工作流程图
class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

workflow = StateGraph(State)
# 第一个工具调用的节点：获取数据库中的表信息
# def first_tool_call(state: State) -> dict[str, list[AIMessage]]:
#     print(state["messages"][0].content)
#     return {
#         "messages": [
#             AIMessage(
#                 content="",  # 设置消息内容为空，工具调用会生成实际结果
#                 tool_calls=[
#                     {
#                         "name": "query_rag",  # 调用的工具名称，获取数据库表
#                         "args": {'query':state["messages"][0].content},  # 无参数调用
#                         "id": "query_rag_id",  # 为工具调用生成唯一 ID
#                     }
#                 ],
#             )
#         ]
#     }
# 定义 Agent 的状态结构，存储消息信息
def chatbot(state: State):
    return {"messages": [query_rag.invoke(state["messages"][0].content)]}

def summ(state: State):
    print(state["messages"][0].content)
    return {"messages": [summary_rag.invoke(state["messages"][0].content)]}

workflow.add_node("chatbot", chatbot) 
workflow.add_node("summ", summ) 
workflow.add_edge(START, "chatbot")
workflow.add_edge("chatbot", "summ")
workflow.add_edge("summ", END)
graph = workflow.compile()

# 开始一个简单的聊天循环
while True:
    # 获取用户输入
    user_input = input("User: ")
    
    # 可以随时通过输入 "quit"、"exit" 或 "q" 退出聊天循环
    if user_input.lower() in ["quit", "exit", "q"]:
        print("Goodbye!")  # 打印告别信息
        break  # 结束循环，退出聊天

    # 将每次用户输入的内容传递给 graph.stream，用于聊天机器人状态处理
    # "messages": ("user", user_input) 表示传递的消息是用户输入的内容
    for event in graph.stream({"messages": ("user", user_input)}):
        # 遍历每个事件的值
        for value in event.values():
            # 打印输出 chatbot 生成的最新消息
            print("Assistant:", value)


# print(query_rag.invoke("如何判断数据变化率是否大于阈值"))