import oracledb
import pandas as pd
from json import load
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores.oraclevs import OracleVS
from langchain_community.vectorstores.utils import DistanceStrategy
from sentence_transformers import CrossEncoder
# import langchain
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


class VectorSearchEngine:
    def __init__(self):
        # print(langchain.__version__)

        config = load(open('../config.json', 'r', encoding='utf-8'))
        # localmodelconfig = config['local_model']

        # print(config)

        vdbconfig = config['vdb_config']
        username = "testuser"
        password = "testuser"
        dsn = "192.168.31.118:1521/orclpdb1"
        mytable_name = "OVS"
        minpool = 1
        maxpool = 10
        increpool = 1
        # print(vdbconfig)

        username = vdbconfig.get('username')
        password = vdbconfig.get('password')
        dsn = vdbconfig.get('dsn')
        self.mytable_name = vdbconfig.get('table_name')
        minpool = vdbconfig.get('poolminxsize')
        maxpool = vdbconfig.get('poolmaxsize')
        increpool = vdbconfig.get('poolincrement')
        self.score = config['rerank_model'].get('score')
        self.upload_dir = config['knowledge_file'].get('upload_dir')
        self.http_url = config['knowledge_file'].get('http_url')
        self.rerank_topN = config['rag_config'].get('rerank_topN')

        # 初始化嵌入模型
        local_model_path = config['embedding_model'].get('path')
        self.embedding_model = SentenceTransformerEmbeddings(
            model_name=local_model_path)

        try:
            connection = oracledb.connect(user=username, password=password, dsn=dsn)
            print("Connection successful!")
            connection.close()
        except Exception as e:
            print("Connection failed!")

        # 数据库连接参数

        self.pool = oracledb.create_pool(user=username, password=password, dsn=dsn, min=minpool, max=maxpool, increment=increpool)
        # connection = pool.acquire()
        # conn = self.pool.acquire()
        # conn = oracledb.connect(user=username, password=password, dsn=dsn)

        # 创建 Oracle 向量存储
        # self.vectorstore = OracleVS(
        #     client=conn,
        #     embedding_function=self.embedding_model,
        #     table_name=self.mytable_name,
        #     distance_strategy=DistanceStrategy.COSINE
        # )

        # 初始化 CrossEncoder 模型
        local_rank_model_path = config['rerank_model'].get('path')
        self.cross_encoder = CrossEncoder(
            model_name=local_rank_model_path, max_length=config['rerank_model'].get('max_length'), device=config['rerank_model'].get('device'))

    def vector_search(self, question, k=3, rankn=3, ranks=0.3):
        # print(self.vectorstore)
        # 执行相似性搜索
        retrieved_docs = ''
        conn = self.pool.acquire()
        self.vectorstore = OracleVS(
            client=conn,
            embedding_function=self.embedding_model,
            table_name=self.mytable_name,
            distance_strategy=DistanceStrategy.COSINE
        )

        retrieved_docs = self.vectorstore.similarity_search(question, k)
        conn.close()

        print("*************************************************************************")
        print("VDB serach条件如下：")
        print("rerank选择排名前" + str(rankn) + "的文档，而且文档打分入选标准score: " + str(ranks) + " ，vdb文档搜索的topk: " + str(k))
        print("*************************************************************************")

        # 使用 CrossEncoder 重新排序
        reranked_docs = self.cross_encoder.rank(
            question,
            ["".join("[" + doc.metadata['source'].replace(self.upload_dir, "").replace("\\", "") + "](" + doc.metadata['source'].replace(self.upload_dir, self.http_url).replace("\\", "/") + ")" + "\n\n" + doc.page_content)
             for doc in retrieved_docs],
            top_k=k,
            return_documents=True
        )

        all_content = ""

        # print(reranked_docs)

        topN_docs = get_topN(reranked_docs, rankn)

        i = 1

        for reranked_doc in topN_docs:
            print("DEBUG>找到文档 " + str(i) + " 打分= : ", reranked_doc["score"])
            i = i + 1

            if float(reranked_doc["score"]) > ranks:
                content = "".join(reranked_doc["text"] + "\n\n")
                print(content[0:100] + " .... 长度:" +
                      str(len(content)) + " ... 略")
                all_content += content
        if len(all_content) < 20:
            all_content = "[Exception: 没有搜索到对应的知识]" + all_content

        return all_content

    def doc_manage(self, cmd_type, file_name):
        print('++++')
        conn = self.pool.acquire()
        all_content = ""

        if cmd_type == "delete":
            with conn.cursor() as cursor:
                # params = {'file_name':file_full_name}
                params = {'file_name': file_name}
                sql = f"select count(*) from {self.mytable_name} a where a.metadata.source = :file_name"
                cursor.execute(sql, params)
                count = cursor.fetchone()[0]
                if count == 0:
                    all_content = "向量数据库没有该文件"
                else:
                    sql = f"delete from {self.mytable_name} a where a.metadata.source = :file_name"
                    cursor.execute(sql, params)
                    conn.commit()
                    all_content = "删除文件成功"
            conn.close()
        elif cmd_type == "check":
            with conn.cursor() as cursor:
                # params = {'file_name':file_full_name}
                params = {'file_name': file_name}
                sql = f"select a.text from {self.mytable_name} a where a.metadata.source = :file_name order by a.id"
                cursor.execute(sql, params)
                for row in cursor:
                    text = row[0].read()
                    content = f'{text} \n {"=" * 100} \n'
                    all_content += content
            conn.close()
            if len(all_content) == 0:
                all_content = "向量数据库没有该文件"
        elif cmd_type == "search":
            if file_name == "*":
                sql = f"select distinct a.metadata.source as name from {self.mytable_name} a"
                all_content = pd.read_sql(sql, conn)
            else:
                lower_file_match = file_name.lower()
                file_match_string = f'%{lower_file_match}%'
                sql = f"select distinct a.metadata.source as name from {self.mytable_name} a where lower(a.metadata.source) like :var_file_match"
                all_content = pd.read_sql(sql, conn, params={"var_file_match": file_match_string})
        else:
            return r"未知的操作类型"

        print(all_content)
        return all_content


def get_topN(reranked_docs, n):
    # Sort the reranked_docs by score in descending order
    sorted_docs = sorted(
        reranked_docs, key=lambda doc: doc['score'], reverse=True)
    # Select the top n documents
    topN_reranked_docs = sorted_docs[:n]
    return topN_reranked_docs


# 定义FastAPI应用
vdbapi = FastAPI()

# 初始化搜索引擎实例
search_engine = VectorSearchEngine()


class SearchRequest(BaseModel):
    question: str
    k: int = 3
    rankn: int = 3
    ranks: float = 0.3


class DocCmdRequest(BaseModel):
    cmd_type: str
    file_name: str


@vdbapi.post("/vector_search/")
def vector_search(request: SearchRequest):
    try:
        answer = search_engine.vector_search(
            request.question, request.k, request.rankn, request.ranks)
        print("----------------向量搜索:--------------\n", request.question)
        print("----------------搜索结果:--------------\n", answer)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@vdbapi.post("/doc_manage/")
def doc_manage(request: DocCmdRequest):
    try:
        result = search_engine.doc_manage(request.cmd_type, request.file_name)
        print("----------------文档管理:--------------\n", request.cmd_type)
        print("----------------文档管理结果:--------------\n", result)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 运行FastAPI应用
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(vdbapi, host="127.0.0.1", port=8989)
