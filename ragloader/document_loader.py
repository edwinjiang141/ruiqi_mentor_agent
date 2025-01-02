import os
import time
import oracledb
from json import load
import pymupdf
import pymupdf4llm
import mammoth
import markdownify

from langchain_community.document_loaders import (
    PyMuPDFLoader,
    TextLoader,
    UnstructuredPowerPointLoader,
    UnstructuredWordDocumentLoader
)

from langchain.text_splitter import (RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter)
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import oraclevs
from langchain_community.vectorstores.oraclevs import OracleVS
from langchain_community.vectorstores.utils import DistanceStrategy
from langchain_core.documents import Document

import streamlit as st

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
embedding_model_path = config["embedding_model"]["path"]

pool = oracledb.create_pool(user=username, password=password, dsn=dsn,min=poolminsize, max=poolmaxsize, increment=poolincrement)

LOADER_MAPPING = {
    ".pdf": (PyMuPDFLoader, {}),
    ".txt": (TextLoader, {"encoding": "utf8"}),
    ".pptx": (UnstructuredPowerPointLoader, {}),
    ".docx": (UnstructuredWordDocumentLoader, {}),
    ".html": (TextLoader, {"encoding": "utf8"}),
}

def load_document(file_path: str):
    name, extension = os.path.splitext(file_path)
    if extension in LOADER_MAPPING:
        loader_class, loader_args = LOADER_MAPPING[extension]
        loader = loader_class(file_path, **loader_args)
        return loader.load()
    raise ValueError(f"Unsupported file extension '{extension}'")
    
def load_pdf_document(file_path: str):
    md_text = pymupdf4llm.to_markdown(file_path)
    
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
        ("####", "Header 4"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on, 
        return_each_line=True,
        strip_headers=False
    )
    
    all_content = ""
    docs = markdown_splitter.split_text(md_text)
    for doc in docs:
        if 'Header 4' in doc.metadata:
           if "描述" in doc.metadata['Header 4']:
               all_content += doc.page_content.replace('####','\n\n')
           if "结果" in doc.metadata['Header 4']:
               all_content += doc.page_content.replace('####','\n\n')
           if "根因" in doc.metadata['Header 4']:
               all_content += doc.page_content.replace('####','\n\n')
           if "解决方案" in doc.metadata['Header 4']:
               all_content += doc.page_content.replace('####','\n\n')
           if "建议" in doc.metadata['Header 4']:
               all_content += doc.page_content.replace('####','\n\n')
           if "后续计划" in doc.metadata['Header 4']:
               all_content += doc.page_content.replace('####','\n\n')
    result_doc = [Document(page_content=all_content, metadata={"source": file_path})]
    return result_doc
    
def ignore_image(image):
    return []
    
# 转存Word文档内的图片
# func是具有一个参数的函数。此参数是要转换的图像元素，并具有以下属性:
# open()				打开图像文件。返回类文件对象。
# content_type	图像的内容类型，如image/png
def convert_image(image):
    with image.open() as image_bytes:
        extension = image.content_type.split("/")[1]
        print(extension)
        image_filename = "./output/image_{0}.{1}".format(str(time.time()),extension)
        print(image_filename)
        with open(image_filename, 'wb') as f:
            f.write(image_bytes.read())
    return {"src":image_filename}
    
def remove_after_character(text, character):
    # 使用split()分割字符串，分割结果是2部分，取分割后的第一部分
    parts = text.split(character, 1)
    return parts[0] if parts else text
    
def load_word_document(file_path: str):

    # 转化Word文档为HTML,忽略图片
    result = mammoth.convert_to_html(file_path, convert_image=ignore_image)
    # 获取HTML内容
    html = result.value
    # 转化HTML为Markdown
    md_text = markdownify.markdownify(html,heading_style="ATX")
    
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
        ("####", "Header 4"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on, 
        return_each_line=True,
        strip_headers=False
    )
    
    all_content = ""
    docs = markdown_splitter.split_text(md_text)
    for doc in docs:
        if 'Header 1' in doc.metadata:
           if "描述" in doc.metadata['Header 1']:
               all_content += doc.page_content.replace('#','\n\n')
           if "结果" in doc.metadata['Header 1']:
               all_content += doc.page_content.replace('#','\n\n')
           if "根因" in doc.metadata['Header 1']:
               all_content += doc.page_content.replace('#','\n\n')
           if "解决方案" in doc.metadata['Header 1']:
               all_content += doc.page_content.replace('#','\n\n')
           if "建议" in doc.metadata['Header 1']:
               all_content += doc.page_content.replace('#','\n\n')
           if "后续计划" in doc.metadata['Header 1']:
               all_content += doc.page_content.replace('#','\n\n')
           if  "后续分析" in doc.metadata['Header 1']:
               all_content += doc.page_content.replace('#','\n\n')
    new_content = remove_after_character(all_content,"Oracle Corporation")
    result_doc = [Document(page_content=new_content, metadata={"source": file_path})]
    return result_doc
    
def load_and_split_oracle_official_manual(file_path: str):
    # 打开PDF文件
    doc=pymupdf.open(file_path)
    # 获取PDF文件的目录结构，针对每一个标题，获取标题级别、标题内容、标题页号
    # Document.get_toc()获取目录(列表)
    # simple=True时，返回简单版本的各级目录，包括
    # lvl 标题层级，从1开始
    # title 标题名称
    # page 跳转到的页码
    # 参考
    # https://pymupdf.readthedocs.io/en/latest/document.html#Document.get_toc
    toc_list = doc.get_toc(simple=True)
    # title_list是一个字典列表
    title_list = []
    for toc in toc_list:
        # 添加新的字典到列表
        title_list.append({'level': toc[0], 'content': toc[1], 'page': toc[2]-1})
    # 针对每一个标题，获取标题内容方框在该页的坐标位置
    # 如果标题内容跨行，每一行会生产一个坐标矩阵，则取第一个坐标矩阵
    for title in title_list:
        content=title["content"]
        page=title["page"]
        rlist = doc[page].search_for(content)
        # 如果找不到，那么截取标题内容的一半，再次查询
        if len(rlist) == 0:
           content_length = int(len(content)/2)
           sub_content = content[0:content_length]
           sub_rlist = doc[page].search_for(sub_content)
           if len(sub_rlist) == 0:
              title['x0']=0
              title['y0']=0
              title['x1']=0
              title['y1']=0
           else:
              title['x0']=sub_rlist[0].x0
              title['y0']=sub_rlist[0].y0
              title['x1']=sub_rlist[0].x1
              title['y1']=sub_rlist[0].y1
        else:
           title['x0']=rlist[0].x0
           title['y0']=rlist[0].y0
           title['x1']=rlist[0].x1
           title['y1']=rlist[0].y1
    # 针对每一个标题，获取标题和标题对应的内容
    docs = []
    for index in range(len(title_list)):
        #最后一个标题
        if index == len(title_list) - 1:
           new_content=get_context_of_last_title(
                  file_path,
                  title_list[index].get('content'),
                  title_list[index].get('page'),
                  title_list[index].get('x0',0),
                  title_list[index].get('y0',0),
                  title_list[index].get('x1',0),
                  title_list[index].get('y1',0)
                  )
        else:
           new_content=get_context(
                  file_path,
                  title_list[index].get('content'),
                  title_list[index].get('page'),
                  title_list[index].get('x0'),
                  title_list[index].get('y0'),
                  title_list[index].get('x1'),
                  title_list[index].get('y1'),
                  title_list[index+1].get('page'),
                  title_list[index+1].get('x0',0),
                  title_list[index+1].get('y0',0),
                  title_list[index+1].get('x1',0),
                  title_list[index+1].get('y1',0)
                  )
        doc = Document(page_content=new_content, metadata={"source": file_path})
        docs.append(doc)
    return docs
    
def get_context(file_path, title, begin_page, begin_position_x0, begin_position_y0, begin_position_x1, begin_position_y1, end_page, end_position_x0, end_position_y0, end_position_x1, end_position_y1):
    # 打开PDF文件
    doc=pymupdf.open(file_path)
    
    all_text = "".join(title + "\n\n")
    
    # 当前标题和下一个标题在同一页
    if begin_page == end_page:
       page = doc[begin_page]
       if end_position_y0 == 0:
          rect = pymupdf.Rect(begin_position_x0, begin_position_y0, doc[begin_page].rect.bottom_right-50)
       else:
          rect = pymupdf.Rect(begin_position_x0, begin_position_y0, doc[begin_page].rect.width, end_position_y0)
       text = page.get_textbox(rect)
       all_text += text
    else:
       # 获取开始页的内容
       page = doc[begin_page]
       # 减去50的目的是，去掉页脚
       rect = pymupdf.Rect(begin_position_x0, begin_position_y0, doc[begin_page].rect.bottom_right-50)
       text = page.get_textbox(rect)
       all_text += text
       # 中间每一页的内容
       for i in range(begin_page+1,end_page):
           page = doc[i]
           text = page.get_text()
           all_text += text
       # 获取结尾页的内容
       page = doc[end_page]
       # 增加50的目的是，去掉页头
       if end_position_y0 == 0:
          rect = pymupdf.Rect(doc[end_page].rect.top_left+50, doc[end_page].rect.bottom_right-50)
       else:
          rect = pymupdf.Rect(doc[end_page].rect.top_left+50, doc[end_page].rect.width, end_position_y0)
       text = page.get_textbox(rect)
       all_text += text
    return all_text
    
def get_context_of_last_title(file_path, title, begin_page, begin_position_x0, begin_position_y0, begin_position_x1, begin_position_y1):
    # 打开PDF文件
    doc=pymupdf.open(file_path)
    
    all_text = "".join(title + "\n\n")
    
    # 获取开始页的内容
    page = doc[begin_page]
    rect = pymupdf.Rect(begin_position_x0, begin_position_y0, doc[begin_page].rect.bottom_right-50)
    text = page.get_textbox(rect)
    all_text += text
    # 之后每一页的内容，直到文档的最后一页
    for i in range(begin_page,len(doc)):
        page = doc[i]
        text = page.get_text()
        all_text += text
    return all_text
    
def load_and_split_oracle_operation_document(file_path: str):
    # b表示加粗，i表示斜体，去掉加粗和斜体
    # 这段代码的作用是去掉了字体的加粗、斜体，带来的***
    custom_styles = """ b =>
                        i => """
    # 转化Word文档为HTML，忽略图片
    result = mammoth.convert_to_html(file_path, style_map=custom_styles, convert_image=ignore_image)
    # 转化Word文档为HTML，提取图片
    # result = mammoth.convert_to_html(file_path, style_map=custom_styles, convert_image=mammoth.images.img_element(convert_image))
    # 获取HTML内容
    html = result.value
    # 转化HTML为Markdown
    md = markdownify.markdownify(html,heading_style="ATX")
    # 获取文件名，没有扩展名，用于写入的html和md文件的文件名
    # file_name_without_ext=os.path.splitext(os.path.basename(file_path))[0]
    # html_filename = "./output/{0}.html".format(file_name_without_ext)
    # md_filename = "./output/{0}.md".format(file_name_without_ext)
    # with open(html_filename,'w',encoding='utf-8') as html_file:
    #      html_file.write(html)
    # with open(md_filename,"w",encoding='utf-8') as md_file:
    #      md_file.write(md)
    
    # word文档的原始结构如下:
    # 3	根因分析
    # 3.2	详细分析
    # 3.2.1	DB告警日志
    # 3.2.2	详细分析
    # 转化为Markdown的结构如下:
    # 根因分析
    # ## 详细分析
    # ### DB告警日志
    # ### 详细分析
    
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
        ("####", "Header 4"),
        ("#####", "Header 5")
    ]
    # strip_headers=True 输出的chunk内容中，去掉标题。
    # return_each_line 针对每个标题，聚合该标题的所有行
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on, 
        return_each_line=False,
        strip_headers=True
    )
    # 输出结果是一个Document列表
    result_doc_list = []
    docs = markdown_splitter.split_text(md)
    # 针对拆分后生成的每个chunk，做一个处理，最终生成一个Document
    for doc in docs:
        #print(doc.metadata)
        #下面这个if条件的作用，过滤掉没有标题的内容，主要是第一页和目录
        if doc.metadata:
           # 遍历该chunk的metadata内容，合并在一起。即针对每个标题，把父标题和子标题连接在一起
           title = "-".join([doc.metadata[key] for key in doc.metadata])
           # 这段代码的作用是解决了inst_id变成inst\_id，sql_id变成sql\_id，*变成\*问题
           # Markdown中的星号和下划线有其他用处，转化为Markdown后，做了转义，即使用\_代替下划线，使用\*代替星号，需要做反向处理
           content = doc.page_content.replace('\_','_').replace('\*','*')
           # 把标题和内容合并在一起，作为Document的page_content
           all_text = "".join(title + "\n" + content)
           i_doc = Document(page_content=all_text, metadata={"source": file_path})
           result_doc_list.append(i_doc)
    
    #text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    #splits = text_splitter.split_documents(md_header_splits)
    return result_doc_list
    
def load_mos_doc(file_path):
    doc=pymupdf.open(file_path)
    all_text = ""
    docs = []
    for i, page in enumerate(doc):
        if i == 0:
           rlist = page.search_for("Copyright")
           if len(rlist) == 0:
              rect = pymupdf.Rect(0, 28, page.rect.width, page.rect.height-28)
              text = page.get_textbox(rect)
              all_text += text
           else:
              rect = pymupdf.Rect(0, rlist[0].y1, page.rect.width, page.rect.height-28)
              text = page.get_textbox(rect)
              all_text += text
        elif i == len(doc) - 1:
           rlist = page.search_for("Community")
           if len(rlist) == 0:
              rect = pymupdf.Rect(0, 28, page.rect.width, page.rect.height-50)
              text = page.get_textbox(rect)
              all_text += text
           else:
              rect = pymupdf.Rect(0, 28, page.rect.width, rlist[0].y0)
              text = page.get_textbox(rect)
              all_text += text
        else:
           rect = pymupdf.Rect(0, 28, page.rect.width, page.rect.height-50)
           text = page.get_textbox(rect)
           all_text += text
    doc = Document(page_content=all_text, metadata={"source": file_path})
    docs.append(doc)
    return docs
    
def split_text(data, chunk_size, chunk_overlap):
    text_splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n"],
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap)
    chunks = text_splitter.split_documents(data)
    return chunks
    
def create_embeddings(chunks):
    embedding_model = SentenceTransformerEmbeddings(model_name=embedding_model_path)
    
    # conn = oracledb.connect(user=username, password=password, dsn=dsn)
    pool = oracledb.create_pool(user=username, password=password, dsn=dsn,min=poolminsize, max=poolmaxsize, increment=poolincrement)
    conn = pool.acquire()
    vectorstore = OracleVS(
          embedding_function=embedding_model,
          client=conn,
          table_name=table_name,
          distance_strategy=DistanceStrategy.COSINE,
    )
    print(chunks)
    vectorstore.add_documents(chunks)
    
    conn.close()
    
def check_single_file_in_vector_database(file_name):
    conn = pool.acquire()
    with conn.cursor() as cursor:
         params = {'file_name':file_name}
         sql = f"select count(*) from {table_name} a where a.metadata.source = :file_name"
         cursor.execute(sql, params)
         count = cursor.fetchone()[0]
         if count == 0:
            result = False
         else:
            result = True
    conn.close()
    return result
    
def update_file_type_in_vector_database(file_name,file_type):
    conn = pool.acquire()
    with conn.cursor() as cursor:
         params = {'file_name':file_name, 'file_type':file_type}
         sql = f"update {table_name} a set a.file_type = :file_type where a.metadata.source = :file_name"
         cursor.execute(sql, params)
         conn.commit()
    conn.close()

# streamlit页面
tab1, tab2, tab3, tab4 = st.tabs([":books:故障报告", ":open_book:官方手册", ":memo:文档(Mos)", ":notebook_with_decorative_cover:运维文档"])
with tab1:
  st.subheader("上传Oracle故障报告")
  uploaded_files = st.file_uploader("请选择上传的文件", type=["pdf","txt","docx","html"], accept_multiple_files=True, key='issue_uploader')
  issue_chunk_size = st.number_input("chunk_size参数:", min_value=100, max_value=2048, value=1000, key='issue_chunk_size')
  issue_chunk_overlap = st.number_input("chunk_overlap参数:", min_value=0, max_value=400, value=0, key='issue_chunk_overlap')
  issue_upload = st.button("开始加载文件", key='issue_button')
  if uploaded_files and issue_upload:
     file_name_list = []
     with st.spinner("正在加载文件、切片和嵌入向量中，请等待"):
       for uploaded_file in uploaded_files:
           file_contents = uploaded_file.read()
           file_name = os.path.join(upload_dir, uploaded_file.name)
           file_name=file_name.replace(' ', '_')
           file_in_vector_database = check_single_file_in_vector_database(file_name)       
           if file_in_vector_database:
              file_name_list.append(file_name)
              continue
           else:
              with open(file_name, 'wb') as f:
                f.write(file_contents)
              name, extension = os.path.splitext(file_name)
              if extension == ".pdf":
                 chunks = load_pdf_document(file_name)
              elif extension == ".docx":
                 chunks = load_word_document(file_name)
              else:
                 data = load_document(file_name)
                 chunks = split_text(data, chunk_size=issue_chunk_size, chunk_overlap=issue_chunk_overlap)
              create_embeddings(chunks)
              update_file_type_in_vector_database(file_name,"故障报告")
     st.success("文件加载、切片和嵌入成功")
     if len(file_name_list) > 0:
        st.write("向量数据库已经有以下文件，所以这次没有加载这些文件")
        for file_name in file_name_list:
            content = f'{file_name} \n'
            st.write(content)

with tab2:
  st.subheader("上传Oracle官方手册")
  uploaded_books = st.file_uploader("请选择上传的文件", type=["pdf"], accept_multiple_files=True, key='book_uploader')
  book_upload_button = st.button("开始加载文件", key='book_button')
  if uploaded_books and book_upload_button:
     file_name_list = []
     with st.spinner("正在加载文件、切片和嵌入向量中，请等待"):
       for uploaded_book in uploaded_books:
           file_contents = uploaded_book.read()
           file_name = os.path.join(upload_dir, uploaded_book.name)
           file_in_vector_database = check_single_file_in_vector_database(file_name)       
           if file_in_vector_database:
              file_name_list.append(file_name)
              continue
           else:
              with open(file_name, 'wb') as f:
                f.write(file_contents)
              chunks = load_and_split_oracle_official_manual(file_name)
              create_embeddings(chunks)
              update_file_type_in_vector_database(file_name,"官方手册")
     st.success("文件加载、切片和嵌入成功")
     if len(file_name_list) > 0:
        st.write("向量数据库已经有以下文件，所以这次没有加载这些文件")
        for file_name in file_name_list:
            content = f'{file_name} \n'
            st.write(content)

with tab3:
  st.subheader("上传MOS文档")
  uploaded_mos = st.file_uploader("请选择上传的文件", type=["pdf"], accept_multiple_files=True, key='mos_uploader')
  mos_chunk_size = st.number_input("chunk_size参数:", min_value=100, max_value=2048, value=1000, key='mos_chunk_size')
  mos_chunk_overlap = st.number_input("chunk_overlap参数:", min_value=0, max_value=400, value=0, key='mos_chunk_overlap')
  mos_upload_button = st.button("开始加载文件", key='mos_button')
  if uploaded_mos and mos_upload_button:
     file_name_list = []
     with st.spinner("正在加载文件、切片和嵌入向量中，请等待"):
       for uploaded_book in uploaded_mos:
           file_contents = uploaded_book.read()
           file_name = os.path.join(upload_dir, uploaded_book.name)
           file_in_vector_database = check_single_file_in_vector_database(file_name)       
           if file_in_vector_database:
              file_name_list.append(file_name)
              continue
           else:
              with open(file_name, 'wb') as f:
                f.write(file_contents)
              data = load_mos_doc(file_name)
              chunks = split_text(data, chunk_size=mos_chunk_size, chunk_overlap=mos_chunk_overlap)
              create_embeddings(chunks)
              update_file_type_in_vector_database(file_name,"MOS文档")
     st.success("文件加载、切片和嵌入成功")
     if len(file_name_list) > 0:
        st.write("向量数据库已经有以下文件，所以这次没有加载这些文件")
        for file_name in file_name_list:
            content = f'{file_name} \n'
            st.write(content)

with tab4:
  st.subheader("上传Oracle运维文档")
  uploaded_operate_docs = st.file_uploader("请选择上传的文件", type=["docx"], accept_multiple_files=True, key='operation_uploader')
  operate_doc_upload_button = st.button("开始加载文件", key='operation_button')
  if uploaded_operate_docs and operate_doc_upload_button:
     file_name_list = []
     with st.spinner("正在加载文件、切片和嵌入向量中，请等待"):
       for uploaded_operate_doc in uploaded_operate_docs:
           file_contents = uploaded_operate_doc.read()
           file_name = os.path.join(upload_dir, uploaded_operate_doc.name)
           file_in_vector_database = check_single_file_in_vector_database(file_name)       
           if file_in_vector_database:
              file_name_list.append(file_name)
              continue
           else:
              with open(file_name, 'wb') as f:
                f.write(file_contents)
              chunks = load_and_split_oracle_operation_document(file_name)
              print(chunks)
              create_embeddings(chunks)
              update_file_type_in_vector_database(file_name,"运维文档")
     st.success("文件加载、切片和嵌入成功")
     if len(file_name_list) > 0:
        st.write("向量数据库已经有以下文件，所以这次没有加载这些文件")
        for file_name in file_name_list:
            content = f'{file_name} \n'
            st.write(content)
            
