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
from langchain.document_loaders.unstructured import UnstructuredFileLoader
from langchain.document_loaders.image import UnstructuredImageLoader
from langchain.text_splitter import CharacterTextSplitter,MarkdownHeaderTextSplitter,RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings
import torch
from .logger import LOG
import ragloader.document_loader_faiss as doc_faiss
import sounddevice as sd
import numpy as np

from werkzeug.utils import secure_filename
from urllib.parse import quote, unquote

from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
) 


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


class Ragloader_Api:
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
            "/backend-api/v2/ragloader": {
                "function": self._ragloader,
                "methods": ["POST"],
            },
            "/backend-api/v2/ragsearch": {
                "function": self._ragsearch,
                "methods": ["GET"],
            },
            "/backend-api/v2/raglist": {   # 🆕 获取 FAISS 数据库中的所有文件
                "function": self._raglist,
                "methods": ["GET"],
            },
            "/backend-api/v2/ragdelete": {  # 🆕 删除选中的文件
                "function": self._ragdelete,
                "methods": ["POST"],
            }
        }
    
    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
    def save_doc_faiss(self,text_splitter):

        enbeddings = OpenAIEmbeddings(openai_api_key = os.environ["OPENAI_API_KEY"],openai_api_base = "https://pro.aiskt.com/v1" )
        print('text_splitter: %s',text_splitter)
        #return FAISS.from_texts(text_splitter, enbeddings)
        return FAISS.from_documents(text_splitter, enbeddings)  
    
    def detect_document_type(self,document_path):

        print('document',document_path)
        guess_file = os.path.splitext(document_path)
        print('guess_file %s',guess_file[1])
        file_type = ""
        image_types = ['jpg', 'jpeg', 'png', 'gif']

        # if(guess_file.extension.lower()  == "pdf"):
        #     file_type = "pdf"
        # elif(guess_file.extension.lower() in image_types):
        #     file_type = "image"
        # elif(guess_file.extension.lower() == "txt"):
        #     file_type = "txt"
        # elif(guess_file.extension.lower() == "md"):
        #     file_type = "md"
        # else:
        #     file_type = "unkown"
        if(guess_file[1]  == ".pdf"):
            file_type = "pdf"
        elif(guess_file[1] in image_types):
            file_type = "image"
        elif(guess_file[1] == ".txt"):
            file_type = "txt"
        elif(guess_file[1] == ".docx"):
            file_type = "docx"
        elif(guess_file[1] == ".md"):
            file_type = "md"
        else:
            file_type = "unkown"

        return file_type

    def _ragloader(self):
        try:
            # 使用管道进行转录或翻译
            doc_files = request.files.get("files")
            # 保存文件
            # 获取原始文件名，并进行URL编码
            original_filename = doc_files.filename
            
            doc_path = os.path.join("/root/mentor_agent/oradoc", original_filename)
            doc_files.save(doc_path)

            category = request.form.get("category")
            LOG.info(f"[upload files is ]：{doc_files}")
            LOG.info(f"[upload category is ]：{category}")
            if not doc_files:
                return jsonify({"status": "error", "message": "未选择文件"})
            

            file_type = self.detect_document_type(doc_path)

            if file_type == 'pdf' and category == 'ora-mos':
                data = doc_faiss.load_mos_doc(doc_path)
                text_splitter = doc_faiss.split_text(data, chunk_size=100, chunk_overlap=10)
            elif file_type == 'docx' and category == 'ora-guzhang':
                text_splitter = doc_faiss.load_word_document(doc_path)
            elif file_type == 'pdf' and category == 'ora-guzhang':
                text_splitter = doc_faiss.load_pdf_document(doc_path)
            elif file_type == 'md' and category == 'ora-guzhang':
                text_splitter = doc_faiss.load_document(doc_path)
            elif file_type == 'docx' and category == 'ora-yunwei':
                text_splitter = doc_faiss.load_and_split_oracle_operation_document(doc_path)
            

            document_search = self.save_doc_faiss(text_splitter)
            #document_search.save_local("troubleshooting_index")
            try:
                enbeddings = OpenAIEmbeddings(openai_api_key = os.environ["OPENAI_API_KEY"],openai_api_base = "https://pro.aiskt.com/v1")
                trouble_index = FAISS.load_local("ora_doc_index", enbeddings, allow_dangerous_deserialization=True)
                trouble_index.merge_from(document_search)
                trouble_index.save_local("ora_doc_index")
            except Exception as e:
                LOG.error(f"处理文件时出错: {e}")
                document_search.save_local("ora_doc_index")
            return "success"
        except Exception as e:
            LOG.error(f"处理文件时出错: {e}")
            self.app.logger.debug(e)
            return {
                "_action": "_ask",
                "success": False,
                "error": f"an error occurred {str(e)}",
            }, 400
        
    # ====================== 新增 RAG 查询方法 ======================
    def _ragsearch(self):
        try:
            query = request.args.get("query", "").strip()
            if not query:
                return jsonify({"status": "error", "message": "查询关键词不能为空"}), 400

            LOG.info(f"Received query: {query}")

            # 加载 FAISS 索引
            embeddings = OpenAIEmbeddings(openai_api_key=os.environ["OPENAI_API_KEY"],
                                        openai_api_base="https://pro.aiskt.com/v1")
            faiss_index = FAISS.load_local("ora_doc_index", embeddings, allow_dangerous_deserialization=True)

            # 进行查询，取前 5 个，然后筛选得分最高的 2 个
            search_results = faiss_index.similarity_search_with_score(query, k=2)
            print(search_results)
            if not search_results:
                return jsonify({"status": "error", "message": "未找到相关结果"}), 404

            # 按相似度得分降序排序（得分越高表示越相似），取最相似的1个结果
            search_results = sorted(search_results, key=lambda x: -x[1])[:1]  # 按得分降序，取最相似的结果
            
            # 解析返回结果
            results = []
            for doc, score in search_results:
                results.append({
                    "document": doc.metadata.get("source", "未知文档"),
                    "content": doc.page_content,
                    "score": float(score)
                })

            return jsonify({"status": "success", "results": results})

        except Exception as e:
            LOG.error(f"查询 FAISS 失败: {str(e)}")
            return jsonify({"status": "error", "message": f"查询失败: {str(e)}"}), 500

    # ====================== 获取 FAISS 数据库中所有文件 ======================
    def _raglist(self):
        try:
            embeddings = OpenAIEmbeddings(openai_api_key=os.environ["OPENAI_API_KEY"],
                                        openai_api_base="https://pro.aiskt.com/v1")
            faiss_index = FAISS.load_local("ora_doc_index", embeddings, allow_dangerous_deserialization=True)

            # ✅ 获取 FAISS 内部索引
            index = faiss_index.index

            # ✅ 检查索引是否为空
            if index is None or index.ntotal == 0:
                return jsonify({"status": "error", "message": "FAISS 索引为空"}), 400

            # ✅ 确保 FAISS 存储的是带有 metadata 的索引
            if not hasattr(faiss_index, "docstore") or not hasattr(faiss_index.docstore, "_dict"):
                return jsonify({"status": "error", "message": "FAISS docstore 结构不匹配"}), 400

            # ✅ 获取所有存储的文件名
            file_list = set()
            for doc_id in faiss_index.docstore._dict.keys():
                metadata = faiss_index.docstore._dict[doc_id].metadata
                if metadata and "source" in metadata:
                    file_list.add(metadata["source"])

            return jsonify({"status": "success", "files": list(file_list)})

        except Exception as e:
            LOG.error(f"获取 FAISS 文件列表失败: {str(e)}")
            return jsonify({"status": "error", "message": f"查询失败: {str(e)}"}), 500




    # ====================== 批量删除 FAISS 向量数据库中的文件 ======================
    def _ragdelete(self):
        try:
            data = request.get_json()
            LOG.info(f"收到前端请求数据: {data}")  # **调试，查看前端是否正确发送 JSON**
            
            files_to_delete = data.get("files", [])
            LOG.info(f"待删除文件: {files_to_delete}")  # **检查 `files_to_delete` 是否有值**

            if not files_to_delete:
                return jsonify({"status": "error", "message": "未选择文件"}), 400

            # **加载 FAISS 索引**
            embeddings = OpenAIEmbeddings(openai_api_key=os.environ["OPENAI_API_KEY"],
                                        openai_api_base="https://pro.aiskt.com/v1")
            faiss_index = FAISS.load_local("ora_doc_index", embeddings, allow_dangerous_deserialization=True)

            # **检查索引是否为空**
            if faiss_index is None or faiss_index.index.ntotal == 0:
                return jsonify({"status": "error", "message": "FAISS 索引为空"}), 400

            # **检查 `docstore` 是否存在**
            if not hasattr(faiss_index, "docstore") or not hasattr(faiss_index.docstore, "_dict"):
                return jsonify({"status": "error", "message": "FAISS docstore 结构不匹配"}), 400

            # **获取要删除的文档索引**
            ids_to_remove = []
            for doc_id in list(faiss_index.docstore._dict.keys()):  # **使用 list() 防止 dict 变动报错**
                metadata = faiss_index.docstore._dict[doc_id].metadata
                if metadata and "source" in metadata and metadata["source"] in files_to_delete:
                    ids_to_remove.append(doc_id)

            # **执行删除**
            if ids_to_remove:
                faiss_index.delete(ids_to_remove)
                faiss_index.save_local("ora_doc_index")  # **保存更新后的索引**
                LOG.info(f"成功删除文件: {files_to_delete}")
            else:
                return jsonify({"status": "error", "message": "未找到匹配的文件"}), 400

            return jsonify({"status": "success", "deleted_files": files_to_delete})

        except Exception as e:
            LOG.error(f"删除 FAISS 文件失败: {str(e)}")
            return jsonify({"status": "error", "message": f"删除失败: {str(e)}"}), 500


