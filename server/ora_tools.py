from json import dumps, loads
from time import time
from hashlib import sha256
from datetime import datetime
from requests import get, post
import os, re
from PIL import Image
import jsonify
import io
import json
import ollama
from .handleFile import readfile
from langchain.embeddings.openai import OpenAIEmbeddings
from werkzeug.utils import secure_filename
from langchain_community.chat_models import ChatOllama
from langchain.vectorstores import FAISS
from .logger import LOG
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
class Oratools:
    def __init__(self, choosedmodel):
        self.choosedmodel = choosedmodel
        
    def check_rag(self,question):
        enbeddings = OpenAIEmbeddings(openai_api_key = os.environ["OPENAI_API_KEY"],openai_api_base = "https://pro.aiskt.com/v1")

        document_search = FAISS.load_local("ora_doc_index", enbeddings,allow_dangerous_deserialization = True)

        search_results = document_search.similarity_search_with_score(question, k=2)
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

        prompt_template = """请仔细阅读以下文本， 不能随意进行更改，仅仅从语法修饰方面进行修改后输出,
        根据知识库已知的信息，一切生成的内容必须都是知识库里的内容，不允许在答案中添加编造成分。不要把模型思考的过程进行输出
            要求：
            1、先按照逻辑顺序，生成一整套流程，不需要进行输出
            2、针对提出的问题，去对应已经生成的这套流程中的某个环节，然后从这个环节及它以后的流程进行输出，避免无效信息的输出。如果问题需要整个流程运行完才能解决，那就输出整个流程
        文本内容：{text}"""
        
        # 使用 ChatOllama 生成问题
        llm = ChatOllama(model=self.choosedmodel, temperature=0.0)
        prompt = PromptTemplate(template=prompt_template, input_variables=["text"])
        chain = prompt | llm
        response = chain.invoke({"text": results[0]['content']})
        return response.content
    
    def ora_tablespace(self,question):
        if "privilege" in question:
            return "function ora_tablespace missing dba privilege"
        elif  "tablespace" in question:
            return self.check_rag(question)
        else:
            return "function ora_tablespace other solution"

    ### 使用工具 ####
    def ora_error(self,question):
        if "ORA-04031" in question:
            return self.check_rag(question)
            return "function ora_error: other solution" 