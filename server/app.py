from flask import (
    Flask,
    jsonify,
    request,
    send_from_directory,
    Response,
    render_template,
    session,
    redirect,
    url_for
)
from json import load, dump
import os,json
from werkzeug.routing import BaseConverter
from flask_cors import CORS


# 自定义正则表达式转换器
class RegexConverter(BaseConverter):
    def __init__(self, map, *args):
        super(RegexConverter, self).__init__(map)
        self.regex = args[0]


app = Flask(__name__, template_folder='./../client/html')
CORS(app)
app.secret_key = "your_secret_key"
app.url_map.converters["regex"] = RegexConverter
# 设置可用的语言
LANGUAGES = {
    "zh_CN": "简体中文",
    "zh_HK": "繁體中文",
    "en_US": "English",
    "ja_JP": "日本語",
    "ko_KR": "한국어",
}


# 加载i18n.json文件
with open("i18n.json", "r", encoding="utf-8") as f:
    translations = json.load(f)

def load_config():
    with  open('config.json', 'r', encoding='utf-8') as file:
        data = load(file)
    return data


@app.route('/')
def index_page():
    print("return to index")
    config = load_config()
    # print(session["language"])
    language_code = session.get("language")

    # 如果 session 中没有设置 language，则使用默认值 "en_US"
    if not language_code:
        language_code = "zh_CN"
        session["language"] = language_code  # 设置默认语言到 session

    print(language_code)

    # language_code = request.args.get("language_code", "en_US")
    # session["language"] = language_code
    language_data = next(
        (lang for lang in translations["languages"] if lang["code"] == language_code),
        None,
    )
    # print(config)
    return render_template(
        "index.html",
        config_options=config,
        lang=language_data["lang"],
        languages=LANGUAGES,
    )


# 语言切换路由，处理 GET 请求
@app.route("/set_language/<language_code>", methods=["GET"])
def set_language(language_code):

    print("----", language_code)
    if language_code in LANGUAGES:

        session["language"] = language_code
    return redirect(url_for("index_page"))


@app.route("/chat/", defaults={"path": None})
@app.route('/chat/<regex("[\w-]+"):path>')
def chat_page(path):
    print("Received path:", path)  # 调试信息
    return redirect(url_for("index_page"))


@app.route('/config')
def config_page():
    return send_from_directory('./../client/html', 'config.html')


@app.route('/readme')
def readme_page():
    return send_from_directory('./../client/html', 'readme.html')


@app.route('/api/config', methods=['GET'])
def get_config():
    with open('config.json', 'r', encoding='utf-8') as file:
        config = load(file)
    return jsonify(config)


@app.route('/api/readme', methods=['GET'])
def get_readme():
    with open('LISENCE.txt', 'r', encoding='utf-8') as file:
        readme = file.read()
    return readme


@app.route('/api/config', methods=['POST'])
def update_config():
    updated_config = request.json
    with open('config.json', 'w', encoding='utf-8') as file:
        dump(updated_config, file, indent=4)
    return jsonify({"status": "success"}), 200
