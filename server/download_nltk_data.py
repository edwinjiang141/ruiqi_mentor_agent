import nltk
import ssl

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# 下载 wordnet 数据集
nltk.download('wordnet')
nltk.download('omw-1.4')  # Open Multilingual Wordnet 