# Filename: test_backend_api.py

import unittest
from unittest.mock import MagicMock, patch
from flask import Flask
from backend import Backend_Api
import json

class TestBackendApi(unittest.TestCase):
    def setUp(self):
        # 初始化测试环境，包括 Flask 应用和配置字典
        self.app = Flask(__name__)
        self.config = {
            "openai_key": "test_openai_key",
            "openai_api_base": "https://api.openai.com/v1/",
            "proxy": None,
            "kimi_api_base": "https://kimi.api/v1/",
            "ollama_model_list": ["ollama-model-1"],
            "kimi_model_list": ["kimi-model-1"],
            "print_conversation": False,
            "ollama_options": {"num_predict": 5}
        }
        self.backend_api = Backend_Api(self.app, self.config)
        self.client = self.app.test_client()

        # 注册用于测试的 API 路由
        for route, options in self.backend_api.routes.items():
            # 遍历 backend_api 中的所有路由，并使用 Flask 的 add_url_rule 方法注册每个路由的 URL、处理函数和请求方法
            print(f"Registering route: {route}, with options: {options}")  # 输出所有的路由值
            self.app.add_url_rule(route, view_func=options['function'], methods=options['methods'])

    @patch("backend.ScenarioAgent")
    def test_conversation_with_ollama_model(self, MockScenarioAgent):
        # 测试使用 Ollama 模型的对话逻辑
        mock_agent = MockScenarioAgent.return_value
        mock_agent.chat_with_history.return_value.content = ["response_chunk_1", "response_chunk_2"]

        # 模拟 POST 请求并发送数据
        response = self.client.post(
            "/backend-api/v2/conversation",
            data={
                "model": "ollama-model-1",
                "meta": json.dumps({
                    "content": {
                        "languageSelect": "en",
                        "parts": [{"content": "Hello"}],
                        "mentor_agent": "physics_mentor",
                        "conversation_id": "12345"
                    }
                })
            }
        )

        # 断言响应的状态码、MIME 类型和内容
        try:
            self.assertEqual(response.status_code, 200, f"Unexpected status code: {response.status_code}, response: {response.data}")
            self.assertEqual(response.mimetype, "text/event-stream", f"Unexpected mimetype: {response.mimetype}")
            self.assertIn(b"response_chunk_1", response.data, "Missing expected response chunk 1")
            self.assertIn(b"response_chunk_2", response.data, "Missing expected response chunk 2")
        except AssertionError as e:
            print(f"Test failed: {e}")
            raise

    @patch("backend.ScenarioAgent")
    def test_conversation_with_missing_meta(self, MockScenarioAgent):
        # 测试缺少 meta 数据的情况
        response = self.client.post(
            "/backend-api/v2/conversation",
            data={}
        )

        # 断言响应的状态码和错误信息
        try:
            self.assertEqual(response.status_code, 400, f"Unexpected status code: {response.status_code}, response: {response.data}")
            self.assertIn(b"Meta data missing", response.data, "Missing expected error message for missing meta data")
        except AssertionError as e:
            print(f"Test failed: {e}")
            raise

    @patch("backend.ScenarioAgent")
    def test_conversation_with_invalid_meta(self, MockScenarioAgent):
        # 测试 meta 数据格式无效的情况（如缺少必要的键）
        response = self.client.post(
            "/backend-api/v2/conversation",
            data={
                "model": "ollama-model-1",
                "meta": json.dumps({
                    "content": {
                        "parts": [{"content": "Hello"}],  # 缺少 languageSelect、mentor_agent、conversation_id
                    }
                })
            }
        )

        # 断言响应的状态码和错误信息
        try:
            self.assertEqual(response.status_code, 400, f"Unexpected status code: {response.status_code}, response: {response.data}")
            self.assertIn(b"Meta data missing required fields", response.data, "Missing expected error message for invalid meta data")
        except AssertionError as e:
            print(f"Test failed: {e}")
            raise

    @patch("backend.ScenarioAgent")
    def test_conversation_with_kimi_model(self, MockScenarioAgent):
        # 测试使用 Kimi 模型的对话逻辑
        mock_agent = MockScenarioAgent.return_value
        mock_agent.chat_with_history.return_value.content = ["response_chunk_1", "response_chunk_2"]

        # 模拟 POST 请求并发送数据
        response = self.client.post(
            "/backend-api/v2/conversation",
            data={
                "model": "kimi-model-1",
                "meta": json.dumps({
                    "content": {
                        "languageSelect": "en",
                        "parts": [{"content": "Hello"}],
                        "mentor_agent": "physics_mentor",
                        "conversation_id": "12345"
                    }
                })
            }
        )

        # 断言响应的状态码、MIME 类型和内容
        try:
            self.assertEqual(response.status_code, 200, f"Unexpected status code: {response.status_code}, response: {response.data}")
            self.assertEqual(response.mimetype, "text/event-stream", f"Unexpected mimetype: {response.mimetype}")
            self.assertIn(b"response_chunk_1", response.data, "Missing expected response chunk 1")
            self.assertIn(b"response_chunk_2", response.data, "Missing expected response chunk 2")
        except AssertionError as e:
            print(f"Test failed: {e}")
            raise

    @patch("backend.ScenarioAgent")
    def test_conversation_with_openai_model(self, MockScenarioAgent):
        # 测试使用 OpenAI 模型的对话逻辑
        mock_agent = MockScenarioAgent.return_value
        mock_agent.chat_with_history.return_value.content = ["response_chunk_1", "response_chunk_2"]

        # 模拟 POST 请求并发送数据
        response = self.client.post(
            "/backend-api/v2/conversation",
            data={
                "model": "openai-model",
                "meta": json.dumps({
                    "content": {
                        "languageSelect": "en",
                        "parts": [{"content": "Hello"}],
                        "mentor_agent": "physics_mentor",
                        "conversation_id": "12345"
                    }
                })
            }
        )

        # 断言响应的状态码、MIME 类型和内容
        try:
            self.assertEqual(response.status_code, 200, f"Unexpected status code: {response.status_code}, response: {response.data}")
            self.assertEqual(response.mimetype, "text/event-stream", f"Unexpected mimetype: {response.mimetype}")
            self.assertIn(b"response_chunk_1", response.data, "Missing expected response chunk 1")
            self.assertIn(b"response_chunk_2", response.data, "Missing expected response chunk 2")
        except AssertionError as e:
            print(f"Test failed: {e}")
            raise

if __name__ == "__main__":
    unittest.main()