
import os
from .logger import LOG
from .minicpm_v_model import chat_with_image
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
        return image_desc
    else:
        file_content = upload_file.read().decode('utf-8')
        return file_content