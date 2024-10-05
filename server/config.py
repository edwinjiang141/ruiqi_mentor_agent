# KB Mentor v1.0,
# Updated by: jiangtao
# Base on https://github.com/xtekky/chatgpt-clone, GNU General Public License v3.0


special_instructions = {
    "default": [
        {
            "role": "user",
            "content": "严格遵守知识库搜索的结果给出答案，如果知识库检索为空，就停止回答",
        },
        {"role": "assistant", "content": "明白和遵循你的指令"},
    ],
    "gpt-dba-1.0": [
        {
            "role": "user",
            "content": "您将使用您的知识来帮助用户。你会尽量采用中文的回答问题。",
        },
        {"role": "assistant", "content": "明白和遵循你的指令"},
    ],
}

special_instructions_en = {
    "default": [
        {
            "role": "user",
            "content": "Hello!Give answers strictly following the results of the knowledge base search, and stop answering if the knowledge base search is empty",
        },
        {"role": "assistant", "content": "instructions applied and understood"},
    ],
    "gpt-dba-1.0": [
        {
            "role": "user",
            "content": "you will use your knowledge to help users.",
        },
        {"role": "assistant", "content": "instructions applied and understood"},
    ],
}
