import os
import oracledb
import streamlit as st
import pandas as pd
from json import load
from streamlit_modal import Modal

#with open("config.json", "r") as f:
with open("../config.json", "r",encoding='utf-8') as f:
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

def delete_document(file_name):
    #file_full_name = os.path.join(upload_dir, file_name)
    conn = pool.acquire()
    with conn.cursor() as cursor:
         #params = {'file_name':file_full_name}
         params = {'file_name':file_name}
         sql = f"select count(*) from {table_name} a where a.metadata.source = :file_name"
         cursor.execute(sql, params)
         count = cursor.fetchone()[0]
         if count == 0:
            context = "向量数据库没有该文件"
         else:
            sql = f"delete from {table_name} a where a.metadata.source = :file_name"
            cursor.execute(sql, params)
            conn.commit()
            context = "删除文件成功"
    conn.close()
    return context

def check_document_chunk(file_name):
    #file_full_name = os.path.join(upload_dir, file_name)
    all_content=""
    conn = pool.acquire()
    with conn.cursor() as cursor:
         #params = {'file_name':file_full_name}
         params = {'file_name':file_name}
         sql = f"select a.text from {table_name} a where a.metadata.source = :file_name order by a.id"
         cursor.execute(sql, params)
         for row in cursor:
             text = row[0].read()
             content = f'{text} \n {"=" * 100} \n'
             all_content += content
    conn.close()
    if len(all_content) == 0:
       all_content = "向量数据库没有该文件"
    return all_content
    
def state_on_click(operation, file_name):
    st.session_state[operation] = file_name
   
# streamlit页面
st.subheader("文档数量")
st.write("功能说明：根据文档类型，统计文档数量")
conn = pool.acquire()
sql = f"select a.file_type,count(distinct a.metadata.source) from {table_name} a group by a.file_type"
df = pd.read_sql_query(sql,conn)
conn.close()
column_config={1:"文档类型",2:"数量"}
st.dataframe(df, column_config=column_config, hide_index=True)

st.subheader("文档查询")
st.write("功能说明：查询文档名称，支持模糊查询，比如：输入是故障，输出结果是文档名称包含故障的所有文档")
file_match = st.text_input('请输入您的文件名', key='file_match')
st.write("查询结果如下")
if file_match:
   conn = pool.acquire()
   with conn.cursor() as cursor:
        if file_match == "*":
   		    sql = f"select distinct a.metadata.source as name from {table_name} a"
   		    df = pd.read_sql(sql,conn)
        else:
           lower_file_match = file_match.lower()
           file_match_string = f'%{lower_file_match}%'
           sql = f"select distinct a.metadata.source as name from {table_name} a where lower(a.metadata.source) like :var_file_match"
           df = pd.read_sql(sql,conn,params={"var_file_match":file_match_string})
   conn.close()
   page_size = 5
   if int(len(df) / page_size) > 0:
   	  total_pages = int(len(df) / page_size)
   else:
      total_pages = 1
   page_number = st.number_input('当前页', min_value=1, max_value=total_pages, value=1, step=1)
   start_index = (page_number - 1) * page_size
   end_index = page_number * page_size
   
   with st.container():
        col1, col2, col3 = st.columns([4, 1, 1])
        col1.markdown('**文档名称**')
        col2.markdown('**分块结果**')
        col3.markdown('**删除文档**')
   for index, row in df.iloc[start_index:end_index].iterrows():
       file_name_with_path = row['NAME']
       file_name = file_name_with_path.rsplit("\\", 1)[-1].rsplit("/", 1)[-1]
       col1.write(file_name)
       col2.button('查看分块结果', key=f'detail{index}', on_click=state_on_click, kwargs={'operation': 'detail', 'file_name': file_name_with_path})
       col3.button('删除文档', key=f'delete{index}', on_click=state_on_click, kwargs={'operation': 'delete', 'file_name': file_name_with_path})

if 'detail' in st.session_state:
    file_name = st.session_state.detail
    all_content = check_document_chunk(file_name)
    detail_modal = Modal(title="文件的分块结果", key="detail_modal_key", max_width=900, padding=0)
    with detail_modal.container():
         st.text_area(label='文件的分块结果', value=all_content, key='file_chunk_result', height=400)
    del st.session_state.detail
    
if 'delete' in st.session_state:
    file_name = st.session_state.delete
    delete_modal = Modal(title="删除文档", key="delete_modal_key", max_width=900, padding=0)
    with delete_modal.container():
         st.markdown("""
                确认删除文档{}？
                """.format(file_name))
         confirm_delete = st.button("确定", key="delete_confirm", on_click=state_on_click, kwargs={'operation': 'confirm', 'file_name': file_name})
    del st.session_state.delete
    
if 'confirm' in st.session_state:
   file_name = st.session_state.confirm
   context = delete_document(file_name)
   confirm_modal = Modal(title="", key="comfirm_modal_key", max_width=200, padding=0)
   with confirm_modal.container():
        st.write(context)
   del st.session_state.confirm
