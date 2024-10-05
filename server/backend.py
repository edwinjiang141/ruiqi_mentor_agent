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
from tavily import TavilyClient
from .handleFile import readfile
from .tavily_search import tavily_search
from .scenario_agent import ScenarioAgent
from langchain_community.chat_models import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage 
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
            upload_file = request.files.get("upload_file")

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
            if upload_file:
                print(
                    "######################################file uploaded############################################"
                )
                # file_content = upload_file.read()
                file_content = readfile(upload_file)
                print(file_content)
                # 处理文件的逻辑
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
                def stream():
                    for chunk in response.content:
                        # chunk_message = chunk.choices[0].delta
                        # if not chunk_message.content:
                        #     continue
                        # # print(chunk_message.content)
                        yield chunk
                return self.app.response_class(stream(), mimetype="text/event-stream")
                # system_prompt = agents.load_prompt()
                # messages = [
                #                 {"role": "system", "content": system_prompt},
                #                 {"role": "user", "content": inputmessage},
                #             ]
                # ollama_stream = ollama.chat(
                #             model=choosedmodel,
                #             # messages=[{'role': 'user', 'content': prompt["content"]}],
                #             messages=messages,
                #             stream=True,
                #             options={"max_tokens": 10000,"temperature": 0, "num_predict": self.num_predict},
                #         )
                # def stream():
                #     for chunk in ollama_stream:
                #         yield chunk["message"]["content"]
                # return self.app.response_class(stream(), mimetype="text/event-stream") 
            elif choosedmodel in self.kimi_modellist:
                client = OpenAI(
                    api_key=os.getenv("KIMI_API_KEY"),
                    base_url=self.kimi_api_base,
                )
                n_temp = float(0)
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
                def stream():
                    for chunk in response.content:
                        # chunk_message = chunk.choices[0].delta
                        # if not chunk_message.content:
                        #     continue
                        # # print(chunk_message.content)
                        yield chunk
                return self.app.response_class(stream(), mimetype="text/event-stream")
            else:
                # 访问OpenAI API
                self.app.logger.debug("Chatgpt llm .........................")
                agents = ScenarioAgent('openai',mentor_agent,choosedmodel,conversation_id)
                response = agents.chat_with_history(inputmessage)
                def stream():
                    for chunk in response.content:
                        # chunk_message = chunk.choices[0].delta
                        # if not chunk_message.content:
                        #     continue
                        # # print(chunk_message.content)
                        yield chunk   

                return self.app.response_class(stream(), mimetype="text/event-stream")
                # system_prompt = agents.load_prompt()
                # messages = [
                #                 {"role": "system", "content": system_prompt},
                #                 {"role": "user", "content": inputmessage},
                #             ]
                # client = OpenAI(api_key = self.openai_key,base_url = "https://pro.aiskt.com/v1/")
                # n_temp = float(0)
                # response = client.chat.completions.create(
                #     model=choosedmodel,
                #     messages=messages,
                #     stream=True
                # )
                # def stream():
                #     for chunk in response:
                #         chunk_message = chunk.choices[0].delta
                #         if not chunk_message.content:
                #             continue
                #         # print(chunk_message.content)
                #         yield chunk_message.content
                # return self.app.response_class(stream(), mimetype="text/event-stream")
            
        except Exception as e:
            self.app.logger.debug(e)
            return {
                "_action": "_ask",
                "success": False,
                "error": f"an error occurred {str(e)}",
            }, 400
