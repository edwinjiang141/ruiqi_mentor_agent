from PIL import Image
from transformers import AutoModel, AutoTokenizer,AutoConfig,AutoModelForCausalLM
from .logger import LOG  # 引入日志模块，用于记录日志
import torch
from accelerate import init_empty_weights, infer_auto_device_map, load_checkpoint_in_model, dispatch_model,load_checkpoint_and_dispatch
from deepseek_vl.models import VLChatProcessor, MultiModalityCausalLM
from deepseek_vl.utils.io import load_pil_images
# 加载模型和分词器
# 这里我们使用 `AutoModel` 和 `AutoTokenizer` 加载模型 'openbmb/MiniCPM-V-2_6-int4'
# 参数 `trust_remote_code=True` 表示信任远程代码（根据模型文档设置）


def chat_with_image(image_file, question='作为图片处理和语言学专家，尽量完整、完全的提取图片中的每一个文字', sampling=False, temperature=0.7, stream=False):
    """
    使用模型的聊天功能生成对图像的回答。
    
    参数:
        image_file: 图像文件，用于处理的图像。
        question: 提问的问题，默认为 '描述下这幅图'。
        sampling: 是否使用采样进行生成，默认为 False。
        temperature: 采样温度，用于控制生成文本的多样性，值越高生成越多样。
        stream: 是否流式返回响应，默认为 False。
        
    返回:
        生成的回答文本字符串。
    """

    # with init_empty_weights():
    #     model = AutoModel.from_pretrained('/root/autodl-tmp/MiniCPM-V-2_6/', trust_remote_code=True)
    #     device_map = infer_auto_device_map(model, max_memory={0: "10GB", 1: "10GB"},no_split_module_classes=['SiglipVisionTransformer', 'Qwen2DecoderLayer'])
    #     device_id = device_map["llm.model.embed_tokens"]
    #     device_map["llm.lm_head"] = device_id # firtt and last layer should be in same device
    #     device_map["vpm"] = device_id
    #     device_map["resampler"] = device_id
    #     device_id2 = device_map["llm.model.layers.26"]
    #     device_map["llm.model.layers.8"] = device_id2
    #     device_map["llm.model.layers.9"] = device_id2
    #     device_map["llm.model.layers.10"] = device_id2
    #     device_map["llm.model.layers.11"] = device_id2
    #     device_map["llm.model.layers.12"] = device_id2
    #     device_map["llm.model.layers.13"] = device_id2
    #     device_map["llm.model.layers.14"] = device_id2
    #     device_map["llm.model.layers.15"] = device_id2
    #     device_map["llm.model.layers.16"] = device_id2
    #     #print(device_map)

    #     model = load_checkpoint_and_dispatch(model, '/root/autodl-tmp/MiniCPM-V-2_6/', dtype=torch.bfloat16, device_map=device_map)
        
    # tokenizer = AutoTokenizer.from_pretrained('/root/autodl-tmp/MiniCPM-V-2_6/', trust_remote_code=True)
    # model.eval()

    # max_memory_each_gpu = '10GiB' # Define the maximum memory to use on each gpu, here we suggest using a balanced value, because the weight is not everything, the intermediate activation value also uses GPU memory (10GiB < 16GiB)

    # gpu_device_ids = [0, 1] # Define which gpu to use (now we have two GPUs, each has 16GiB memory)

    # no_split_module_classes = ['SiglipVisionTransformer', 'Qwen2DecoderLayer']

    # max_memory = {
    #     device_id: max_memory_each_gpu for device_id in gpu_device_ids
    # }

    # config = AutoConfig.from_pretrained(
    #     '/root/autodl-tmp/MiniCPM-V-2_6/', 
    #     trust_remote_code=True
    # )

    # tokenizer = AutoTokenizer.from_pretrained(
    #     '/root/autodl-tmp/MiniCPM-V-2_6/', 
    #     trust_remote_code=True
    # )

    # with init_empty_weights():
    #     model = AutoModel.from_config(
    #         config, 
    #         torch_dtype=torch.float16, 
    #         trust_remote_code=True
    #     )

    # device_map = infer_auto_device_map(
    #     model,
    #     max_memory=max_memory, no_split_module_classes=no_split_module_classes
    # )

    # print("auto determined device_map", device_map)

    # # Here we want to make sure the input and output layer are all on the first gpu to avoid any modifications to original inference script.

    # device_map["llm.model.embed_tokens"] = 0
    # device_map["llm.model.layers.0"] = 0
    # device_map["llm.lm_head"] = 0
    # device_map["vpm"] = 0
    # device_map["resampler"] = 0
    # for k,v in device_map.items():
    #     if k.startswith("llm.model.layers.17"):
    #         device_map[k] = 0

    # print("modified device_map", device_map)
    # load_checkpoint_in_model(
    #     model, 
    #     '/root/autodl-tmp/MiniCPM-V-2_6/', 
    #     device_map=device_map)

    # model = dispatch_model(
    #     model, 
    #     device_map=device_map
    # )

    # torch.set_grad_enabled(False)

    # model.eval()

  
    # model = AutoModel.from_pretrained('/root/autodl-tmp/MiniCPM-V-2_6-int4/', trust_remote_code=True)
    # model = model.eval()                                
    # tokenizer = AutoTokenizer.from_pretrained('/root/autodl-tmp/MiniCPM-V-2_6-int4/', trust_remote_code=True)

    torch.manual_seed(0)
    model = AutoModel.from_pretrained('/root/autodl-tmp/MiniCPM-V-2_6/', trust_remote_code=True,attn_implementation='sdpa', torch_dtype=torch.bfloat16)
    model = model.eval().cuda()                                  
    tokenizer = AutoTokenizer.from_pretrained('/root/autodl-tmp/MiniCPM-V-2_6/', trust_remote_code=True, device_map={"": 1})

    # 加载deepseek 模型
    # specify the path to the model
    # model_path = "/root/autodl-tmp/deepseek-vl2-tiny"
    # vl_chat_processor: VLChatProcessor = VLChatProcessor.from_pretrained(model_path)
    # tokenizer = vl_chat_processor.tokenizer

    
    # model: MultiModalityCausalLM = AutoModelForCausalLM.from_pretrained(model_path, trust_remote_code=True)
    # model = model.to(torch.bfloat16).cuda().eval()
    
    #model.eval()  # 设置模型为评估模式，以确保不进行训练中的随机性操作
    # 打开并转换图像为 RGB 模式
    image = Image.open(image_file).convert('RGB')

    # 创建消息列表，模拟用户和 AI 的对话
    msgs = [{'role': 'user', 'content': [image, question]}]

    # 如果不启用流式输出，直接返回生成的完整响应
    if not stream:
        return model.chat(image=None, msgs=msgs, tokenizer=tokenizer, temperature=temperature)
    else:
        # 启用流式输出，则逐字生成并打印响应
        generated_text = ""
        for new_text in model.chat(image=None, msgs=msgs, tokenizer=tokenizer, sampling=sampling, temperature=temperature, stream=True):
            generated_text += new_text
            print(new_text, flush=True, end='')  # 实时输出每部分生成的文本
        return generated_text  # 返回完整的生成文本

# 主程序入口
if __name__ == "__main__":
    import sys  # 引入 sys 模块以获取命令行参数
    if len(sys.argv) != 2:
        print("Usage: python src/minicpm_v_model.py <image_file>")  # 提示正确的用法
        sys.exit(1)  # 退出并返回状态码 1，表示错误

    image_file = sys.argv[1]  # 获取命令行传入的图像文件路径
    question = 'What is in the image?'  # 定义默认问题
    response = chat_with_image(image_file, question, sampling=True, temperature=0.7, stream=True)  # 调用生成响应函数
    print("\nFinal Response:", response)  # 输出最终响应
