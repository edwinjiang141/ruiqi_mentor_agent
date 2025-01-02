import os
import time
import oracledb
from json import load

from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import oraclevs
from langchain_community.vectorstores.oraclevs import OracleVS
from langchain_community.vectorstores.utils import DistanceStrategy
from langchain_core.documents import Document

from sentence_transformers import CrossEncoder

import streamlit as st

from openai import OpenAI
client = OpenAI(
api_key="sk-6ffTGsNO4XCIwlBkdqf7ir3xNC0mLpco4M5GT5lUEFoOdPof",
base_url="https://api.moonshot.cn/v1",
)

with open("../config.json", "r") as f:
	config = load(f)
f.close()
dsn = config["vdb_config"]["dsn"]
username = config["vdb_config"]["username"]
password = config["vdb_config"]["password"]
table_name = config["vdb_config"]["table_name"]
poolminsize = config["vdb_config"]["poolminsize"]
poolmaxsize = config["vdb_config"]["poolmaxsize"]
poolincrement = config["vdb_config"]["poolincrement"]
embedding_model_path = config["embedding_model"]["path"]
rerank_model_path = config["rerank_model"]["path"]
rerank_model_max_length = config["rerank_model"]["max_length"]
rerank_model_device = config["rerank_model"]["device"]
rerank_model_score = config["rerank_model"]["score"]

upload_dir = config["knowledge_file"]["upload_dir"]
download_method = config["knowledge_file"]["download_method"]
http_url = config["knowledge_file"]["http_url"]

def oracle23ai_vector_search(question, k=3):
    
    embedding_model = SentenceTransformerEmbeddings(model_name=embedding_model_path)
    # conn = oracledb.connect(user=username, password=password, dsn=dsn)
    pool = oracledb.create_pool(user=username, password=password, dsn=dsn,min=poolminsize, max=poolmaxsize, increment=poolincrement)
    conn = pool.acquire()
    vectorstore = OracleVS(
      client=conn,
      embedding_function=embedding_model,
      table_name=table_name,
      distance_strategy=DistanceStrategy.COSINE
    )
    
    retrieved_docs = vectorstore.similarity_search(question, k)
    conn.close()
    return retrieved_docs
    
def rerank_function(question, docs, k=3):
    cross_encoder = CrossEncoder(
      model_name=rerank_model_path, max_length=rerank_model_max_length, device=rerank_model_device
    )
    
    if download_method == "http":
       reranked_docs = cross_encoder.rank(
         question,
         ["".join(doc.metadata['source'].replace(upload_dir,http_url) + "\n\n" + doc.page_content) for doc in docs],
         top_k=k,
         return_documents=True
       )
    else:
       reranked_docs = cross_encoder.rank(
         question,
         ["".join(doc.metadata['source'] + "\n\n" + doc.page_content) for doc in docs],
         top_k=k,
         return_documents=True
       )
    
    chunks = []
    for reranked_doc in reranked_docs:
      #print(reranked_doc["score"])
      #print(reranked_doc["text"])
      if float(reranked_doc["score"]) > float(rerank_model_score):
        # 将文本按行分割成列表， 然后获取第一行，第一行的内容是chunk的来源文档
        lines = reranked_doc["text"].split('\n')
        first_line = lines[0]
        score=reranked_doc["score"]
        score=f'{score:0.2f}'
        doc = Document(page_content=reranked_doc["text"], metadata={"source": first_line, "score": score})
        chunks.append(doc)
    return chunks
    
def merge_chunk_content(chunks):
    all_content=""
    for chunk in chunks:
        content = "".join(chunk.page_content + "\n\n")
        all_content += content
    return all_content
    
def merge_chunk_content_with_score(chunks):
    all_content=""
    for chunk in chunks:
        content = "".join("chunk的分数:" + chunk.metadata['score'] + "\n" + chunk.page_content + "\n\n")
        all_content += content
    return all_content
    
def generate_download_button(chunks):
    # 去重
    res_list = []
    for chunk in chunks:
        if chunk.metadata['source'] not in res_list:
           res_list.append(chunk.metadata['source'])
    # 针对每个参考文档，输出下载按钮
    for item in res_list:
        file_name = item.rsplit("/", 1)[-1]
        file_path = os.path.join(upload_dir, file_name)
        if os.path.exists(file_path):
           with open(file_path, "rb") as file:
                document = file.read()
           st.download_button(label=f"{file_name}",data=document,file_name=f"{file_name}",on_click=None)
        else:
           st.text(f"{file_path} 不存在")
        	 
def ask_llm_and_get_answer(question, vector_search_result, temperature=0.5):
    prompt = f"""请使用以下上下文来回答最后的问题。如果你不知道答案，就说你不知道，不要试图编造答案。请在答案的最后，列出参考文档。
已知内容:
------------------------------------------------------------------------------
    {vector_search_result}
------------------------------------------------------------------------------
问题:
*************************
    {question}
*************************
"""
    #print(prompt)
    messages = [{"role": "system", "content": "你是一个Oracle知识库的人工智能助手"},
                {"role": "user", "content": prompt}]
    response = client.chat.completions.create(
               model="moonshot-v1-8k",
               messages=messages,
               temperature=temperature,
               )
    return response.choices[0].message.content
    
def clear_history():
    if 'history' in st.session_state:
        del st.session_state['history']

# streamlit页面
k_tip_markdown = '''
向量查询时，返回与问题最相似的k个向量。
'''.strip()
temperature_tip_markdown = '''
temperature参数  
控制大语言模型LLM输出的随机程度。  
取值在0~1之间。  
当接近0时，预测的随机性会较低，产生更保守、可预测的文本。  
当接近1时，预测的随机性会较高，所有词被选择的可能性更大，会产生更有创意、多样化的文本。  
例如：  
当我们需要精准解答数学问题，我们应该使用较低的temperature，比如0。  
当我们需要撰写创意文案，我们应该使用较高的temperature，比如1。
'''.strip()
with st.sidebar:
     k = st.number_input("k参数", min_value=1, max_value=20, value=3, help=k_tip_markdown, on_change=clear_history)
     temperature = st.number_input("temperature参数", min_value=0.0, max_value=1.0, value=0.5, step=0.01, help=temperature_tip_markdown)
client_question = st.text_input('请输入您的问题', key='question')
if client_question:
   start_time = time.time()
   docs = oracle23ai_vector_search(client_question, k)
   end_time = time.time()
   elapsed_time = end_time - start_time
   vs_time = f'向量数据库查询耗时(单位:秒) {elapsed_time:0.2f}'
   
   start_time = time.time()
   chunks=rerank_function(client_question, docs, k)
   end_time = time.time()
   elapsed_time = end_time - start_time
   rerank_time = f'rerank耗时(单位:秒) {elapsed_time:0.2f}'
   
   context_after_vs=merge_chunk_content(docs)
   context_after_rerank=merge_chunk_content_with_score(chunks)
   context_for_llm=merge_chunk_content(chunks)
   
   start_time = time.time()
   answer = ask_llm_and_get_answer(client_question, context_for_llm, temperature)
   end_time = time.time()
   elapsed_time = end_time - start_time
   llm_time = f'大语言模型耗时(单位:秒) {elapsed_time:0.2f}'
   
   all_time = "".join(vs_time + "\n" + rerank_time + "\n" + llm_time)
   
   # 输出前台内容
   st.text_area(label='时间消耗情况', value=all_time, key='all_time', height=20)
   
   st.text_area(label='Oracle 23ai向量查询结果', value=context_after_vs, key='context_after_vs', height=400)
   
   st.text_area(label='Rerank结果', value=context_after_rerank, key='context_after_rerank', height=400)
   
   value = f'问题: \n {client_question} \n 答案: \n {answer}'
   
   if 'history' not in st.session_state:
      st.session_state.history = f'{value} \n {"-" * 100} \n'
   else:
      st.session_state.history = f'{value} \n {"-" * 100} \n {st.session_state.history}'
   h = st.session_state.history
   st.text_area(label='大语言模型结果', value=h, key='history', height=400)
   
   st.divider()
   st.subheader("下载知识库文件")
   generate_download_button(chunks)