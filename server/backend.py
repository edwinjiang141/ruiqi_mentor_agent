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
from flask import Flask, jsonify,send_file
import ollama
import numpy as np
# from tavily import TavilyClient
from .handleFile import readfile
# from .tavily_search import tavily_search
from .scenario_agent import ScenarioAgent
from .ora_tools import Oratools
from .code_assistant_agent import CodeAssistantAgent
from langchain_community.chat_models import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage 
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chains import RetrievalQA
import torch
from .logger import LOG
from playsound import playsound
import sounddevice as sd
import numpy as np
from pydub import AudioSegment
from transformers import (
    AutomaticSpeechRecognitionPipeline,BitsAndBytesConfig,
    WhisperForConditionalGeneration,
    WhisperTokenizer,
    WhisperProcessor,
    pipeline,
)
from werkzeug.utils import secure_filename
from langchain.vectorstores import FAISS
import re
from docx import Document
from openai import OpenAI
#音频处理
# 模型名称和参数配置
# model_name_or_path = "/root/autodl-tmp/models/whisper-large-v2"  # Whisper 模型名称
# BATCH_SIZE = 8  # 处理批次大小
# language = "chinese"
# language_abbr = "zh-CN"
# task = "transcribe"
# # 检查是否可以使用 GPU，否则使用 CPU
# device = "cuda:0" if torch.cuda.is_available() else "cpu"

# # 初始化语音识别管道
# _compute_dtype_map = {
#     'fp32': torch.float32,
#     'fp16': torch.float16,
#     'bf16': torch.bfloat16
# }

# # QLoRA 量化配置
# q_config = BitsAndBytesConfig(load_in_4bit=True,
#                               bnb_4bit_quant_type='nf4',
#                               bnb_4bit_use_double_quant=True,
#                               bnb_4bit_compute_dtype=_compute_dtype_map['bf16'])

# model = WhisperForConditionalGeneration.from_pretrained(
#     model_name_or_path, load_in_8bit=True, device_map=device
# )


# model = WhisperForConditionalGeneration.from_pretrained(model_name_or_path,
#                                   quantization_config=q_config,
#                                   device_map='auto',
#                                   trust_remote_code=True)

# # model = PeftModel.from_pretrained(model, peft_model_path)
# tokenizer = WhisperTokenizer.from_pretrained(
#     model_name_or_path, language=language, task=task
# )
# processor = WhisperProcessor.from_pretrained(
#     model_name_or_path, language=language, task=task
# )
# feature_extractor = processor.feature_extractor
# forced_decoder_ids = processor.get_decoder_prompt_ids(language=language, task=task)
# pipe = AutomaticSpeechRecognitionPipeline(
#     model=model, tokenizer=tokenizer, feature_extractor=feature_extractor,
# )

# pipe = pipeline(
#     task="automatic-speech-recognition",  # 自动语音识别任务
#     model=MODEL_NAME,  # 指定模型
#     chunk_length_s=60,  # 每个音频片段的长度（秒）
#     device=device,  # 指定设备
# )


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


## make docx file from file content


def create_word_document_link(text, DOWNLOAD_FOLDER,conversation_id):
    if not os.path.exists(DOWNLOAD_FOLDER):
        os.makedirs(DOWNLOAD_FOLDER)
    word_filename = os.path.join(DOWNLOAD_FOLDER,conversation_id+'.docx')
    if os.path.exists(word_filename):
        doc = Document(word_filename)  # 读取已有 Word 文件
    else:
        doc = Document()  # 创建新 Word 文件
    doc.add_paragraph(text)
    doc.save(word_filename)

    return word_filename


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
            },
            "/backend-api/v2/audioconver": {
                "function": self._audioconver,
                "methods": ["POST"],
            }
        }


    def _audioconver(self):
        try:
            # 使用管道进行转录或翻译
            audio_file = request.files.get('audio')
            # 保存文件
            filename = secure_filename(audio_file.filename)
            audio_path = os.path.join("/root/mentor_agent/audio", filename)
            # 检查文件是否存在并删除
            if os.path.exists(audio_path):
                try:
                    os.remove(audio_path)  # 删除旧文件
                    time.sleep(0.1)  # 短暂等待，确保删除生效
                except Exception as e:
                    print(f"删除文件失败: {e}")
            audio_file.save(audio_path)
            result = pipe(
                audio_path,
                batch_size=BATCH_SIZE,
                generate_kwargs={"forced_decoder_ids": forced_decoder_ids},
                return_timestamps=True
            )
            text = result["text"]
            LOG.info(f"[识别结果]：{text}")
            
            return text
        except Exception as e:
            LOG.error(f"处理音频文件时出错: {e}")
            self.app.logger.debug(e)
            return {
                "_action": "_ask",
                "success": False,
                "error": f"an error occurred {str(e)}",
            }, 400
        
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
                total_content=''
                # file_content = upload_file.read()
                file_content = ''
                answer = ""
                for file_ in upload_file:
                    file_content,file_ext = readfile(file_,inputmessage)
                    if file_ext.endswith('.txt'):
                        # 使用大语言模型生成问题的提示词
                        prompt_template = """请仔细阅读以下文本， 基于文本内容表达的中心含义，提出一个问题.
                        文本内容：{text}"""
                        
                        # 使用 ChatOllama 生成问题
                        llm = ChatOllama(model=choosedmodel, temperature=0.0)
                        prompt = PromptTemplate(template=prompt_template, input_variables=["text"])
                        chain = prompt | llm
                        response = chain.invoke({"text": file_content})
                        question = response.content
                        # 处理文件的逻辑
                    # DOWNLOAD_FOLDER = 'download_folder/'
                    # create_word_document_link(file_content, DOWNLOAD_FOLDER,conversation_id)
                    # doc_link = 'http://127.0.0.1:6006/download/'+conversation_id+'.docx'

                    # if choosedmodel in self.ollamalist:
                    #     agents = ScenarioAgent('ollama',mentor_agent,choosedmodel,conversation_id)
                    # else:
                    #     agents = ScenarioAgent('kimi',mentor_agent,choosedmodel,conversation_id)
                    
                   
                    if mentor_agent in ('ora_doc','ora_awr'):
                        # enbeddings = OpenAIEmbeddings(openai_api_key = os.environ["OPENAI_API_KEY"],openai_api_base = "https://pro.aiskt.com/v1")
                        # #当向量数据库中没有合适答案时，使用大语言模型能力
                        # LOG.info(f"mentor_agent: {mentor_agent}")
                        
                        # document_search = FAISS.load_local("ora_doc_index", enbeddings,allow_dangerous_deserialization = True)

                        #LOG.info(f"收到前端请求的问题是: {question}")

                        # search_results = document_search.similarity_search_with_score(question, k=2)
                        # if not search_results:
                        #     return jsonify({"status": "error", "message": "未找到相关结果"}), 404

                        # search_results = sorted(search_results, key=lambda x: x[1])[:1]  # 按距离升序，取最相近的 2 个

                        # # 解析返回结果
                        # results = []
                        # for doc, score in search_results:
                        #     results.append({
                        #         "document": doc.metadata.get("source", "未知文档"),
                        #         "content": doc.page_content,
                        #         "score": float(score)
                        #     })
                        
                        # LOG.info(f"收到前端请求数据: {results}")
                        # prompt_template = """请仔细阅读以下文本， 不能随意进行更改，仅仅从语法修饰方面进行修改后输出,
                        # 根据知识库已知的信息，一切生成的内容必须都是知识库里的内容，不允许在答案中添加编造成分。不要把模型思考的过程进行输出
                        #     要求：
                        #     1、先按照逻辑顺序，生成一整套流程，不需要进行输出
                        #     2、针对提出的问题，去对应已经生成的这套流程中的某个环节，然后从这个环节及它以后的流程进行输出，避免无效信息的输出。如果问题需要整个流程运行完才能解决，那就输出整个流程
                        # 文本内容：{text}"""
                        
                        # llm = ChatOllama(model=choosedmodel, temperature=0.0)
                        # prompt = PromptTemplate(template=prompt_template, input_variables=["text"])
                        # chain = prompt | llm
                        # response = chain.invoke({"text": results[0]['content']})
                        # answer = answer+response.content+"\n\n"

                        
                        tools = [
                                    {
                                        "type": "function",
                                        "function": {
                                            "name": "ora_tablespace",
                                            "description": "分析关于表空间报错的问题",
                                            "parameters": {
                                                "type": "object",
                                                "properties": {
                                                    "question": {
                                                        "type": "string",
                                                        "description": "问题描述"
                                                    }
                                                },
                                                "required": ["question"]
                                            },
                                        }
                                    },
                                    {
                                        "type": "function",
                                        "function": {
                                            "name": "ora_error",
                                            "description": "分析关于ORA 的报错",
                                            "parameters": {
                                                "type": "object",
                                                "properties": {
                                                    "question": {
                                                        "type": "string",
                                                        "description": "问题描述"
                                                    }
                                                },
                                                "required": ["question"] 
                                            },
                                        }
                                    },
                                ]
                        messages = [
                                        {"role": "user", "content":question}
                                    ]
                        
                        

                        def send_messages(messages):
                            response = client.chat.completions.create(
                                model="deepseek-chat",
                                messages=messages,
                                tools=tools,
                                tool_choice="auto"
                            )
                            return response.choices[0].message

                        client = OpenAI(
                            api_key=os.getenv("DEEPSEEK_API_KEY"),
                            base_url="https://api.deepseek.com",
                        )
                        message = send_messages(messages)
                        # messages.append(message)
                        # print(message.tool_calls[0])
                        function_args = json.loads(message.tool_calls[0].function.arguments)
                        print(function_args['question'])
                        oratool = Oratools(choosedmodel)
                        if message.tool_calls[0].function.name == 'ora_error':
                            answer =oratool.ora_error(function_args['question'])
                        elif message.tool_calls[0].function.name == 'ora_tablespace':
                            answer = oratool.ora_tablespace(function_args['question'])
                        # print(tool)
                        # print(message.tool_calls[0].id)
                        # messages.append({"role": "tool", "tool_call_id": message.tool_calls[0].id, "content": question})
                        # message = send_messages(messages)

                        # print(f"Model>\t {message}")
                        # answer = message.content
                    elif mentor_agent in ('data_analysis'):

                        prompt_template = """根据输入的数据库一周的系统负载数据, 进行如下分析：
                                            第一步，先根据时间分布，先对各列数据进行分析，找出特征点，对整体数据进行分类，并列出具体的数据说明，给出每种类别的描述。
                                            第二步，根据数据和分类的特征，比较基于多元状态估计的MSET算法和随即森林、Z-score异常检测 这三个算法，找出最合适的算法，并给出基于上述系统负载数据的科学解释。
                                            第三步 然后用这个确定的异常检测算法，分析数据中是否存在异常点并输出异常点数据的信息，找出不超过2个最明显的异常点，用表格的形式列出改异常点的异常输出。并给出合理的解释
                                            """
                        
                        # 使用 ChatOllama 生成问题
                        # llm = ChatOllama(model=choosedmodel, temperature=0.0)
                        # prompt = PromptTemplate(template=prompt_template, input_variables=["text"])
                        # chain = prompt | llm
                        # response = chain.invoke({"text": file_content})
                        # answer = response.content
                        client = OpenAI(
                            api_key=os.getenv("DEEPSEEK_API_KEY"),
                            base_url="https://api.deepseek.com",
                        )

                        response = client.chat.completions.create(
                            model="deepseek-chat",
                            messages=[
                                {"role": "system", "content": prompt_template},
                                {"role": "user", "content": file_content},
                            ],
                            stream=False
                        )
                        
                        findings = response.choices[0].message.content
                        prompt_template = """请仔细阅读以下检测结果， 依据对异常点的解释.要求总结成一个技术问题：目的是如何解决发现的异常点以及造成异常的原因
                        例如按照如下样例格式输出：
                        异常点1（时间）：
                            异常现象：
                            可能原因：
                            解决方案：
                        文本内容：{text}"""
                        
                        # 使用 ChatOllama 生成问题
                        llm = ChatOllama(model=choosedmodel, temperature=0.0)
                        prompt = PromptTemplate(template=prompt_template, input_variables=["text"])
                        chain = prompt | llm
                        response = chain.invoke({"text": findings})
                        question = response.content
                        print(f"question: {question}")
                        oratool = Oratools(choosedmodel)
                        solution = oratool.check_rag(question)
                        answer = findings + question
                    else:
                        agents = ScenarioAgent('ollama',mentor_agent,choosedmodel,conversation_id)
                        answer = agents.chat_with_history(inputmessage+'  '+file_content)
                        import time
                        def string_generator(long_string, chunk_size=10):
                            return (long_string[i:i + chunk_size] for i in range(0, len(long_string), chunk_size))
                        def stream():
                            # for chunk in response.content:
                            #     yield chunk
                            for chunk in string_generator(answer.content):
                                yield chunk
                                time.sleep(0.2)  # 模拟流式输出的延迟
                            
                            # if doc_link:
                            #     yield f"\n\n文档链接:\n\n<a href='{doc_link}' target='_blank'>{doc_link}</a>\n\n"

                        return self.app.response_class(stream(), mimetype="text/event-stream")
                import time
                def string_generator(long_string, chunk_size=10):
                    return (long_string[i:i + chunk_size] for i in range(0, len(long_string), chunk_size))
                def stream():
                    # for chunk in response.content:
                    #     yield chunk
                    for chunk in string_generator(answer):
                        yield chunk
                        time.sleep(0.2)  # 模拟流式输出的延迟
                    
                    # if doc_link:
                    #     yield f"\n\n文档链接:\n\n<a href='{doc_link}' target='_blank'>{doc_link}</a>\n\n"

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
                    
                    code_writer = code_generate_prompt | ChatOllama(model=choosedmodel,max_tokens=32768, temperature=0.8)

                    try:
                        with open("prompts/code_assistant_prompt.txt", "r", encoding="utf-8") as file:
                            code_assistant_prompt = ChatPromptTemplate.from_messages([
                                            ("system", file.read().strip()),  # 系统提示部分
                                            MessagesPlaceholder(variable_name="messages"),  # 消息占位符
                                        ])
                    except FileNotFoundError:
                        raise FileNotFoundError(f"Prompt file {self.prompt_file} not found!")
                    
                    code_flect = code_assistant_prompt | ChatOllama(model=choosedmodel,max_tokens=32768, temperature=0.8)
                    
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
                elif mentor_agent == 'ora_doc':
                    enbeddings = OpenAIEmbeddings(openai_api_key = os.environ["OPENAI_API_KEY"],openai_api_base = "https://pro.aiskt.com/v1")
                    #当向量数据库中没有合适答案时，使用大语言模型能力
                    LOG.info(f"mentor_agent: {mentor_agent}")
                    # prompt_template = """ <指令>根据知识库已知的信息，一切生成的内容必须都是知识库里的内容，不允许在答案中添加编造成分，按照如下格式输出:
                    #                     1 问题或者故障现象是什么 2 影响或者风险是什么 3 需要收集哪些必要的信息和日志 3 应急处理步骤，包括相关的操作系统命令、SQL查询语句等
                    #                     一切生成的内容必须都是知识库里的内容，不允许在答案中添加编造成分，答案请使用中文。 </指令>
                    #                     <已知信息>{context}</已知信息>
                    #                     <问题>{question}</问题>
                    #                 """
                    
                    # prompt_template = """ <指令>根据知识库已知的信息，一切生成的内容必须都是知识库里的内容，不允许在答案中添加编造成分，
                    #                     一切生成的内容必须都是知识库里的内容，不允许在答案中添加编造成分，答案请使用中文。 </指令>
                    #                     <已知信息>{context}</已知信息>
                    #                     <问题>{question}</问题> 
                    #                 """
                    
                    # prompt = PromptTemplate(template = prompt_template,input_variables=["context", "question"])

                    document_search = FAISS.load_local("ora_doc_index", enbeddings,allow_dangerous_deserialization = True)

                    # #llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0,openai_organization = "org-cODSJjftWgVspplR3MwUi2HN",openai_api_key = os.environ["OPENAI_API_KEY"])
                    # llm = ChatOllama(model=choosedmodel,max_tokens=8192, temperature=0)
                    # #llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0,openai_api_key = os.environ["OPENAI_API_KEY"],openai_api_base = "https://pro.aiskt.com/v1")
                    # qa_chain = RetrievalQA.from_llm(llm,
                    #                             retriever=document_search.as_retriever(search_type="similarity_score_threshold", 
                    #                                                         search_kwargs={"score_threshold": 0.3, "k": 1}),prompt=prompt)
                    # # qa_chain.combine_documents_chain.document_prompt = PromptTemplate(input_variables=["query"],template="{page_content}")
                    # qa_chain.return_source_documents=True
                    # result = qa_chain({"query": inputmessage})
                    search_results = document_search.similarity_search_with_score(inputmessage, k=2)
                    if not search_results:
                        return jsonify({"status": "error", "message": "未找到相关结果"}), 404

                    search_results = sorted(search_results, key=lambda x: -x[1])[:1]  # 按距离升序，取最相近的 2 个

                    # 解析返回结果
                    results = []
                    for doc, score in search_results:
                        results.append({
                            "document": doc.metadata.get("source", "未知文档"),
                            "content": doc.page_content,
                            "score": float(score)
                        })
                    
                    LOG.info(f"收到前端请求数据: {results}")
                    # agents = ScenarioAgent('ollama',mentor_agent,choosedmodel,conversation_id)
                    # if not result["source_documents"]:
                    #     response = agents.chat_with_history(inputmessage)
                    #     LOG.info(f"没有发现相关文档")
                    # else:
                    #     response = agents.chat_with_history(result['result']+' Quesion is :'+inputmessage)
                    prompt_template = """请仔细阅读以下文本， 不能随意进行更改，仅仅从语法修饰方面进行修改后输出,
                    根据知识库已知的信息，一切生成的内容必须都是知识库里的内容，不允许在答案中添加编造成分。不要把模型思考的过程进行输出
                        要求：
                        1、先按照逻辑顺序，生成一整套流程，不需要进行输出
                        2、针对提出的问题，去对应已经生成的这套流程中的某个环节，然后从这个环节及它以后的流程进行输出，避免无效信息的输出。如果问题需要整个流程运行完才能解决，那就输出整个流程
                    文本内容：{text}"""
                    
                    # 使用 ChatOllama 生成问题
                    llm = ChatOllama(model=choosedmodel, temperature=0.0)
                    prompt = PromptTemplate(template=prompt_template, input_variables=["text"])
                    chain = prompt | llm
                    response = chain.invoke({"text": results[0]['content']})
                    answer = response.content
                        

                    
                    import time

                    def string_generator(long_string, chunk_size=10):
                        return (long_string[i:i + chunk_size] for i in range(0, len(long_string), chunk_size))
                    
                    def stream():
                        for chunk in string_generator(answer):
                            yield chunk
                            time.sleep(0.2)  # 模拟流式输出的延迟
                    return self.app.response_class(stream(), mimetype="text/event-stream")
                else:
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
                elif mentor_agent == 'ora_doc':
                    enbeddings = OpenAIEmbeddings(openai_api_key = os.environ["OPENAI_API_KEY"],openai_api_base = "https://pro.aiskt.com/v1")
                    #当向量数据库中没有合适答案时，使用大语言模型能力
                    LOG.info(f"mentor_agent: {mentor_agent}")
                    # prompt_template = """ <指令>根据知识库已知的信息，一切生成的内容必须都是知识库里的内容，不允许在答案中添加编造成分，按照如下格式输出:
                    #                     1 问题或者故障现象是什么 2 影响或者风险是什么 3 需要收集哪些必要的信息和日志 3 应急处理步骤，包括相关的操作系统命令、SQL查询语句等
                    #                     一切生成的内容必须都是知识库里的内容，不允许在答案中添加编造成分，答案请使用中文。 </指令>
                    #                     <已知信息>{context}</已知信息>
                    #                     <问题>{question}</问题>
                    #                 """
                    
                    prompt_template = """ <指令>根据知识库已知的信息，一切生成的内容必须都是知识库里的内容，不允许在答案中添加编造成分，
                                        一切生成的内容必须都是知识库里的内容，不允许在答案中添加编造成分，答案请使用中文。 </指令>
                                        <已知信息>{context}</已知信息>
                                        <问题>{question}</问题> 
                                    """
                    
                    prompt = PromptTemplate(template = prompt_template,input_variables=["context", "question"])

                    document_search = FAISS.load_local("ora_doc_index", enbeddings,allow_dangerous_deserialization = True)

                    #llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0,openai_organization = "org-cODSJjftWgVspplR3MwUi2HN",openai_api_key = os.environ["OPENAI_API_KEY"])
                    llm = ChatOllama(model=choosedmodel,max_tokens=8192, temperature=0.8)
                    #llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0,openai_api_key = os.environ["OPENAI_API_KEY"],openai_api_base = "https://pro.aiskt.com/v1")
                    qa_chain = RetrievalQA.from_llm(llm,
                                                retriever=document_search.as_retriever(search_type="similarity_score_threshold",
                                                                            search_kwargs={"score_threshold": 0.2}),prompt=prompt)
                    # qa_chain.combine_documents_chain.document_prompt = PromptTemplate(input_variables=["query"],template="{page_content}")
                    qa_chain.return_source_documents=True
                    result = qa_chain({"query": inputmessage})
                    
                    LOG.info(f"收到前端请求数据: {result}")
                    agents = ScenarioAgent('kimi',mentor_agent,choosedmodel,conversation_id)
                    if not result["source_documents"]:
                        response = agents.chat_with_history(inputmessage)
                        LOG.info(f"没有发现相关文档")
                    else:
                        response = agents.chat_with_history(result['result']+' Quesion is :'+inputmessage)
                        

                    
                    import time

                    def string_generator(long_string, chunk_size=10):
                        return (long_string[i:i + chunk_size] for i in range(0, len(long_string), chunk_size))
                    
                    def stream():
                        for chunk in string_generator(response.content):
                            yield chunk
                            time.sleep(0.2)  # 模拟流式输出的延迟
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
                    LOG.info(f"response content,{response.content}")
                    # Step 1. Instantiating your TavilyClient
                    # from tavily import TavilyClient
                    # client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

                    # # Step 2. Executing a simple search query
                    # web_response = client.search(inputmessage,include_images=True)

                    # # Step 3. That's it! You've done a Tavily Search!
                    # print(web_response['images'][1])
                    #response = response+web_result
                    client = OpenAI(api_key = os.environ["OPENAI_API_KEY"],base_url = "https://pro.aiskt.com/v1")  # 初始化 OpenAI 客户端
                    
                    # # 加载音频文件
                    # audio = AudioSegment.from_mp3(file_path)

                    # # 将音频转换为 numpy 数组
                    # samples = np.array(audio.get_array_of_samples())

                    # # 播放音频
                    # sd.play(samples, audio.frame_rate)
                    # sd.wait()  # 等待播放结束

                    # 生成音频 2025-01-18
                    if os.path.exists("tts_text.mp3"):
                        os.remove("tts_text.mp3")
                    else:
                        pass
                    with client.audio.speech.with_streaming_response.create(
                        model="tts-1",
                        voice = "nova",
                        input = response.content
                    ) as responseaudio:
                        responseaudio.stream_to_file("tts_text.mp3")
                    file_path = os.path.join(os.getcwd(), 'tts_text.mp3') 
                    LOG.debug(f"[pwd]:{file_path}")
                    #playsound(file_path)
                     # 生成音频 2025-01-18
                    
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
