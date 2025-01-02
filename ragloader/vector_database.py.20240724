import os
import oracledb
import streamlit as st
from json import load

with open("../config.json", "r") as f:
	config = load(f)
f.close()
upload_dir = config["knowledge_file"]["upload_dir"]
dsn = config["vdb_config"]["dsn"]
username = config["vdb_config"]["username"]
password = config["vdb_config"]["password"]
table_name = config["vdb_config"]["table_name"]
poolminsize = config["vdb_config"]["poolminsize"]
poolmaxsize = config["vdb_config"]["poolmaxsize"]
poolincrement = config["vdb_config"]["poolincrement"]
pool = oracledb.create_pool(user=username, password=password, dsn=dsn,min=poolminsize, max=poolmaxsize, increment=poolincrement)

st.subheader("知识库文件的分块结果")
knowledge_file = st.text_input('请输入您的知识库文件名', key='knowledge_file')
if knowledge_file:
   file_name = os.path.join(upload_dir, knowledge_file)
   all_content=""
   conn = pool.acquire()
   with conn.cursor() as cursor:
        params = {'file_name':file_name}
        sql = "select a.text from ovs_new a where a.metadata.source = :file_name order by a.id"
        cursor.execute(sql, params)
        for row in cursor:
            text = row[0].read()
            content = f'{text} \n {"=" * 100} \n'
            all_content += content
   conn.close()
   if len(all_content) == 0:
      all_content = "向量数据库没有该知识库文件"
   st.text_area(label='知识库文件的分块结果', value=all_content, key='knowledge_file_chunks', height=400)