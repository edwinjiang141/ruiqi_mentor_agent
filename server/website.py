# 导入必要的模块和函数
from flask import render_template, send_file, redirect
from time import time
from os import urandom

# 定义Website类


class Website:
    # 初始化方法，传入Flask应用实例
    def __init__(self, app) -> None:
        self.app = app
        # 定义API路由
        self.routes = {
            '/': {
                'function': lambda: redirect('/chat'),  # 根路径重定向到/chat
                'methods': ['GET', 'POST']  # 支持GET和POST请求
            },
            '/chat/': {
                'function': self._index,  # 处理/chat/路径的请求
                'methods': ['GET', 'POST']  # 支持GET和POST请求
            },
            '/chat/<conversation_id>': {
                'function': self._chat,  # 处理/chat/<conversation_id>路径的请求
                'methods': ['GET', 'POST']  # 支持GET和POST请求
            },
            '/assets/<folder>/<file>': {
                'function': self._assets,  # 处理/assets/<folder>/<file>路径的请求
                'methods': ['GET', 'POST']  # 支持GET和POST请求
            }
        }

    # 处理/chat/<conversation_id>路径的请求
    def _chat(self, conversation_id):
        if not '-' in conversation_id:  # 检查conversation_id是否包含'-'
            return redirect(f'/chat')  # 不包含则重定向到/chat
        # 渲染index.html模板并传入chat_id
        return render_template('index.html', chat_id=conversation_id)

    # 处理/chat/路径的请求
    def _index(self):
        # 生成一个随机的chat_id并渲染index.html模板
        return render_template('index.html', chat_id=f'{urandom(4).hex()}-{urandom(2).hex()}-{urandom(2).hex()}-{urandom(2).hex()}-{hex(int(time() * 1000))[2:]}')

    # 处理/assets/<folder>/<file>路径的请求
    def _assets(self, folder: str, file: str):
        try:
            # 尝试发送指定路径的文件
            return send_file(f"./../client/{folder}/{file}", as_attachment=False)
        except:
            # 如果文件未找到，返回404错误
            return "File not found", 404
