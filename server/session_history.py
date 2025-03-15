from langchain_core.chat_history import (
    BaseChatMessageHistory,  # 基础聊天消息历史类
    InMemoryChatMessageHistory,  # 内存中的聊天消息历史类
)
from langchain_core.runnables.history import RunnableWithMessageHistory  # 导入带有消息历史的可运行类
from langchain_community.chat_message_histories import RedisChatMessageHistory
from .logger import LOG
REDIS_URL = "redis://localhost:6379/0"
# 用于存储会话历史的字典
store = {}

def get_session_history(session_id: str) -> RedisChatMessageHistory:
    """
    获取指定会话ID的聊天历史。如果该会话ID不存在，则创建一个新的聊天历史实例。
    
    参数:
        session_id (str): 会话的唯一标识符
    
    返回:
        BaseChatMessageHistory: 对应会话的聊天历史对象
    """
    if session_id not in store:
        # 如果会话ID不存在于存储中，创建一个新的内存聊天历史实例
        store[session_id] = RedisChatMessageHistory(session_id, url=REDIS_URL)
    # 打印会话的完整聊天记录
    try:
        redis_history = store[session_id]
        messages = redis_history.messages  # 假设messages存储的是全部聊天记录
        print(f"{messages}")
    except Exception as e:
        LOG.error(f"Error fetching chat history for session {session_id}: {e}")

    return store[session_id]