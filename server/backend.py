# KB Mentor v1.0,
# Updated by: JiangTao
# Base on https://github.com/xtekky/chatgpt-clone, GNU General Public License v3.0

from json import dumps, loads
from time import time
from flask import request
from hashlib import sha256
from datetime import datetime
from openai import OpenAI
from requests import get, post
import os, re
from PIL import Image
import jsonify
import io
import json
from flask import Flask, jsonify
import ollama
import numpy as np
# from tavily import TavilyClient
from .handleFile import readfile
# from .tavily_search import tavily_search
from .scenario_agent import ScenarioAgent
from .code_assistant_agent import CodeAssistantAgent
from langchain_community.chat_models import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage 
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
# 定义Backend_Api类
def get_recent_conversations(conversation, num_rounds=3):
    # 每轮对话包括两条消息：'user' 和 'assistant'
    if num_rounds == 0:
        # 返回指定的前面三条消息
        return []
    num_messages = num_rounds * 2
    return conversation[-num_messages:]


def get_current_time_in_milliseconds():
    now = datetime.now()
    current_milliseconds = now.microsecond // 1000
    total_milliseconds = current_milliseconds
    return total_milliseconds


class Backend_Api:
    # 初始化方法，传入Flask应用实例和配置字典
    def __init__(self, app, config: dict) -> None:
        self.app = app
        # 获取OpenAI的API密钥和API基础URL
        self.openai_key = os.getenv("OPENAI_API_KEY") or config["openai_key"]
        self.openai_api_base = os.getenv("OPENAI_API_BASE") or config["openai_api_base"]
        self.proxy = config["proxy"]
        self.kimi_key = os.getenv("KIMI_API_KEY")
        # 初始化 VectorSearchEngine
        # self.search_engine = VectorSearchEngine()
        # other parameter
        self.kimi_api_base = config["kimi_api_base"]
        self.ollamalist = config["ollama_model_list"]
        self.kimi_modellist = config["kimi_model_list"]
        self.print_conversation = config["print_conversation"]
        self.num_predict = config["ollama_options"].get("num_predict")
        # 定义API路由
        self.routes = {
            "/backend-api/v2/conversation": {
                "function": self._conversation,
                "methods": ["POST"],
            }
        }

    # 定义内部方法_conversation，处理对话请求

    def _conversation(self):
        try:
            choosedmodel = request.form.get("model")
            meta = request.form.get("meta")
            upload_file = request.files.getlist("upload_file")

            if meta:
                meta = json.loads(meta)
                print(json.dumps(meta, indent=4))
            else:
                print(request.form)
                return jsonify({"status": "error", "message": "Meta data missing"}), 400

            # 解析 meta 中的数据
            internet_access = True
            languageSelect = meta["content"]["languageSelect"]
            prompt = meta["content"]["parts"][0]
            inputmessage = prompt["content"]
            mentor_agent = meta["content"]["mentor_agent"]
            conversation_id = meta["content"]["conversation_id"]
            print(mentor_agent)
            print(conversation_id)
            
            file_content = ""

            print("languageSelect", languageSelect)

            # 处理文件内容（如果有文件上传）

            if len(upload_file) > 0:
                print(
                    "######################################file uploaded############################################"
                )
                # file_content = upload_file.read()
                file_content = ''
                for file_ in upload_file:
                    file_content += readfile(file_,inputmessage)+'\n'
                    print(file_content)
                    # 处理文件的逻辑
                import time
                def string_generator(long_string, chunk_size=10):
                    return (long_string[i:i + chunk_size] for i in range(0, len(long_string), chunk_size))
                def stream():
                    # for chunk in response.content:
                    #     yield chunk
                    for chunk in string_generator(file_content):
                        yield chunk
                        time.sleep(0.2)  # 模拟流式输出的延迟

                return self.app.response_class(stream(), mimetype="text/event-stream")
            else:
                file_content = ""  # 或者设置为其他默认值

            """
            ************************************************************************************************************************************
            *                                    LLM调用模型如下                                         *
            ************************************************************************************************************************************
            """

            if choosedmodel in self.ollamalist:
                # agents = {
                #             "physics_mentor": ScenarioAgent("physics_mentor"), # 物理导师场景代理
                #             "physics_exam": ScenarioAgent("physics_exam"), # 模拟考试场景代理
                #         }
                
                agents = ScenarioAgent('ollama',mentor_agent,choosedmodel,conversation_id)
                response = agents.chat_with_history(inputmessage)
                import time

                def string_generator(long_string, chunk_size=10):
                    return (long_string[i:i + chunk_size] for i in range(0, len(long_string), chunk_size))
                
                def stream():
                    # for chunk in response.content:
                    #     yield chunk
                    for chunk in string_generator(response.content):
                        yield chunk
                        time.sleep(0.2)  # 模拟流式输出的延迟

                return self.app.response_class(stream(), mimetype="text/event-stream")
            elif choosedmodel in self.kimi_modellist:

                client = OpenAI(
                    api_key=os.getenv("KIMI_API_KEY"),
                    base_url=self.kimi_api_base,
                )
                n_temp = float(0)
                if mentor_agent == 'code_generate':
                    inputs = {
                                    "messages": [
                                        HumanMessage(content=inputmessage)
                                    ],
                             }
                    try:
                        with open("prompts/code_generate_prompt.txt", "r", encoding="utf-8") as file:
                            code_generate_prompt = ChatPromptTemplate.from_messages([
                                            ("system", file.read().strip()),  # 系统提示部分
                                            MessagesPlaceholder(variable_name="messages"),  # 消息占位符
                                        ])
                    except FileNotFoundError:
                        raise FileNotFoundError(f"Prompt file {self.prompt_file} not found!")
                    
                    code_writer = code_generate_prompt | ChatOpenAI(model=choosedmodel, temperature=0,api_key=os.getenv("KIMI_API_KEY"),openai_api_base = os.getenv("KIMI_API_BASE"),streaming=True)

                    try:
                        with open("prompts/code_assistant_prompt.txt", "r", encoding="utf-8") as file:
                            code_assistant_prompt = ChatPromptTemplate.from_messages([
                                            ("system", file.read().strip()),  # 系统提示部分
                                            MessagesPlaceholder(variable_name="messages"),  # 消息占位符
                                        ])
                    except FileNotFoundError:
                        raise FileNotFoundError(f"Prompt file {self.prompt_file} not found!")
                    
                    code_flect = code_assistant_prompt | ChatOpenAI(model=choosedmodel, temperature=0,api_key=os.getenv("KIMI_API_KEY"),openai_api_base = os.getenv("KIMI_API_BASE"),streaming=True)
                    
                    code_agents = CodeAssistantAgent(code_writer,code_flect,inputs)
                    response = code_agents.generate_code()
                    for event in response:
                        if 'writer' in event:
                            generate_md = "#### 写作生成:\n"
                            for message in event['writer']['messages']:
                                generate_md += f"- {message.content}\n"
                        
                        # 如果是反思评论部分
                        if 'reflect' in event:
                            reflect_md = "#### 评论反思:\n"
                            for message in event['reflect']['messages']:
                                reflect_md += f"- {message.content}\n"

                    def string_generator(long_string, chunk_size=10):
                        return (long_string[i:i + chunk_size] for i in range(0, len(long_string), chunk_size))

                    def stream():
                        # for chunk in response.content:
                        #     yield chunk
                        for chunk in string_generator(generate_md+reflect_md):
                            yield chunk
                            

                    return self.app.response_class(stream(), mimetype="text/event-stream")
                else:
                    agents = ScenarioAgent('kimi',mentor_agent,choosedmodel,conversation_id)
                    # system_prompt = agents.load_prompt()
                    # messages = [
                    #                 {"role": "system", "content": system_prompt},
                    #                 {"role": "user", "content": inputmessage},
                    #             ]
                    # response = client.chat.completions.create(
                    #     model=choosedmodel,
                    #     messages=messages,
                    #     temperature=n_temp,
                    #     stream=True,
                    # )
                    #agents.start_new_session()
                    response = agents.chat_with_history(inputmessage)
                    
                    # Step 1. Instantiating your TavilyClient
                    # from tavily import TavilyClient
                    # client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

                    # # Step 2. Executing a simple search query
                    # web_response = client.search(inputmessage,include_images=True)

                    # # Step 3. That's it! You've done a Tavily Search!
                    # print(web_response['images'][1])
                    #response = response+web_result
                    import time

                    def string_generator(long_string, chunk_size=10):
                        return (long_string[i:i + chunk_size] for i in range(0, len(long_string), chunk_size))
                    
                    def stream():
                        for chunk in string_generator(response.content):
                            yield chunk
                            time.sleep(0.2)  # 模拟流式输出的延迟
                    return self.app.response_class(stream(), mimetype="text/event-stream")
            else:
                # 访问OpenAI API
                if mentor_agent == 'code_generate':
                    inputs = {
                                    "messages": [
                                        HumanMessage(content=inputmessage)
                                    ],
                             }
                    try:
                        with open("prompts/code_generate_prompt.txt", "r", encoding="utf-8") as file:
                            code_generate_prompt = ChatPromptTemplate.from_messages([
                                            ("system", file.read().strip()),  # 系统提示部分
                                            MessagesPlaceholder(variable_name="messages"),  # 消息占位符
                                        ])
                    except FileNotFoundError:
                        raise FileNotFoundError(f"Prompt file {self.prompt_file} not found!")
                    
                    code_writer = code_generate_prompt | ChatOpenAI(model=choosedmodel, temperature=0,openai_api_base = os.getenv("OPENAI_API_BASE"),streaming=True)

                    try:
                        with open("prompts/code_assistant_prompt.txt", "r", encoding="utf-8") as file:
                            code_assistant_prompt = ChatPromptTemplate.from_messages([
                                            ("system", file.read().strip()),  # 系统提示部分
                                            MessagesPlaceholder(variable_name="messages"),  # 消息占位符
                                        ])
                    except FileNotFoundError:
                        raise FileNotFoundError(f"Prompt file {self.prompt_file} not found!")
                    
                    code_flect = code_assistant_prompt | ChatOpenAI(model=choosedmodel, temperature=0,openai_api_base = os.getenv("OPENAI_API_BASE"),streaming=True)
                    
                    code_agents = CodeAssistantAgent(code_writer,code_flect,inputs)
                    response = code_agents.generate_code()

                    # def track_steps(func):
                    #     step_counter = {'count': 0}  # 用于记录调用次数
                        
                    #     def wrapper(event, *args, **kwargs):
                    #         # 增加调用次数
                    #         step_counter['count'] += 1
                    #         # 调用原始函数
                    #         return func(event, *args, **kwargs)
                        
                    #     return wrapper

                    # # 使用装饰器装饰 pretty_print_event_markdown 函数
                    # @track_steps
                    def pretty_print_event_markdown(event):
                        # 如果是生成写作部分
                        if 'writer' in event:
                            generate_md = "#### 写作生成:\n"
                            for message in event['writer']['messages']:
                                generate_md += f"- {message.content}\n"
                            return generate_md
                        
                        # 如果是反思评论部分
                        if 'reflect' in event:
                            reflect_md = "#### 评论反思:\n"
                            for message in event['reflect']['messages']:
                                reflect_md += f"- {message.content}\n"
                            return reflect_md

                    def string_generator(long_string, chunk_size=10):
                        return (long_string[i:i + chunk_size] for i in range(0, len(long_string), chunk_size))
                    import time
                    def stream():
                        # for chunk in response.content:
                        #     yield chunk
                        for event in response:
                            for chunk in string_generator(pretty_print_event_markdown(event)):
                                yield chunk
                                time.sleep(0.2) 

                    return self.app.response_class(stream(), mimetype="text/event-stream")
                else:
                    self.app.logger.debug("Chatgpt llm .........................")
                    agents = ScenarioAgent('openai',mentor_agent,choosedmodel,conversation_id)
                    response = agents.chat_with_history(inputmessage)
                    print(response.content)
                    import time

                    def string_generator(long_string, chunk_size=10):
                        return (long_string[i:i + chunk_size] for i in range(0, len(long_string), chunk_size))
                    
                    def stream():
                        # for chunk in response.content:
                        #     yield chunk
                        for chunk in string_generator(response.content):
                            yield chunk
                            time.sleep(0.2)  # 模拟流式输出的延迟

                    return self.app.response_class(stream(), mimetype="text/event-stream")

            
        except Exception as e:
            self.app.logger.debug(e)
            return {
                "_action": "_ask",
                "success": False,
                "error": f"an error occurred {str(e)}",
            }, 400
