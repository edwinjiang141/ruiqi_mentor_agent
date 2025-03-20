
import os
from .logger import LOG
from .minicpm_v_model import chat_with_image
from .ora_awr_parse import parse_awr_report,dict_to_text
def readfile(upload_file,inputmessage):
    print(f"[File Type is ]:{type(upload_file)}")
    file_ext = os.path.splitext(upload_file.filename)[1].lower()
    save_path = os.path.join('.', upload_file.filename)
    upload_file.save(save_path)
    
    if file_ext in ('.jpg', '.png', '.jpeg'):
        if inputmessage:
            image_desc = chat_with_image(upload_file.filename, inputmessage)
        else:
            image_desc = chat_with_image(upload_file.filename)
        return image_desc,file_ext
    elif file_ext.endswith('.html'):
        LOG.info(f"file_ext: {file_ext}")
        upload_file.seek(0)  # 确保指针在文件开头
        
        combined_dict = parse_awr_report(upload_file.filename)
        # 将字典数据转换为文本格式
        text_output = dict_to_text(combined_dict)

        # file_content = upload_file.read()  # 读取文件内容
        # if isinstance(file_content, bytes):
        #     file_content = file_content.decode('utf-8')  # 解码成字符串
        return text_output,file_ext  # 返回HTML内容
    elif file_ext.endswith('.txt'):
        with open(upload_file.filename, 'r', encoding='utf-8') as f:
            file_content = f.read()
        return file_content,file_ext
    elif file_ext.endswith('.csv'):
        with open(upload_file.filename, 'r', encoding='utf-8') as f:
            file_content = f.read()
        return file_content,file_ext
        