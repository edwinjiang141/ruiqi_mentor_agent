import os
import json

i18n = {}
i19n = {}

def get_i18n(reload=False):
    global i18n
    if reload or not i18n:
        i18n = {}
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_file = os.path.join(current_dir, '../../i18n.json')
        config_file = os.path.normpath(config_file)
        with open(config_file, 'r', encoding='utf8') as f:
            i18n = json.load(f)
    return i18n

def get_i19n(reload=False):
    global i19n
    if reload or not i19n:
        i19n = {}
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_file = os.path.join(current_dir, '../../../../configs/alt-mol.json')
        config_file = os.path.normpath(config_file)
        with open(config_file, 'r', encoding='utf8') as f:
            i19n = json.load(f)

    # Update i19n with new data from list_json_contents
    update_i19n_with_json_contents("Stable-diffusion")
    update_i19n_with_json_contents("Lora")

    return i19n

def list_json_contents(modeltype):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    checkpoint_dir = os.path.join(current_dir, '../../../../models/'+modeltype)  
    checkpoint_dir = os.path.normpath(checkpoint_dir)
    json_results = {}

    for root, dirs, files in os.walk(checkpoint_dir):
        json_files = [f for f in files if f.endswith('.json')]

        for json_file in json_files:
            file_path = os.path.join(root, json_file)
            with open(file_path, 'r', encoding='utf8') as file:
                data = json.load(file)
                safe_tensor_filename = json_file.replace('.json', '.safetensors')
                safe_tensor_desc = format_json_as_sentence(data)
                json_results[safe_tensor_filename] = safe_tensor_desc

    return json_results

def update_i19n_with_json_contents(modeltype):
    new_contents = list_json_contents(modeltype)
    for filename, description in new_contents.items():
        if filename not in i19n['languages'][0]['lang']:
            i19n['languages'][0]['lang'][filename] = description
        else:
            i19n['languages'][0]['lang'][filename] += ", " + description

def format_json_as_sentence(data):
    sentences = []
    for key, value in data.items():
        if isinstance(value, dict):
            sentence = format_json_as_sentence(value)
        elif key == 'activation text':
            sentence = f"{{{value}}}"
        else:
            sentence = f"{key}:{value}\n"
        sentences.append(sentence)
    return ', '.join(sentences)

# def main():
#     print(get_i19n())  # 打印更新后的 i19n 来验证输出

# if __name__ == '__main__':
#     main()
