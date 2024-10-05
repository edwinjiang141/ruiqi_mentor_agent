from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import sys

class tavily_search:
    def __init__(self,llm_model: any = None,query: str = None,languageSelect: str = None):
        self.llm_model = llm_model
        self.query = query
        self.languageSelect = languageSelect


    def web_search(self):
        try:
            tavily_tool = TavilySearchResults(max_results=2,search_depth="advanced")
            # doc_search_prompt =ChatPromptTemplate.from_template("""
            #                 according to question, Search only in oracle official documentation web site https://docs.oracle.com or https://blogs.oracle.com and database type only is oracle database,then search releated document
            #                 Question: {question}
            #                 """)
            doc_search_prompt =ChatPromptTemplate.from_template("""
                            languageSelect: 用相应的{languageSelect}来回答
                            在答案后增加这句话: 目前知识库搜搜不到改问题合理的解释，以上答案是从Oracle 的 https://docs.oracle.com or https://blogs.oracle.com 搜索得到，请参考。
                            Question: {question}
                            """)
            llm = ChatOllama(
                model=self.llm_model,
                temperature=0,
            )
            # 将生成的查询传递给最终答案的提交工具
            # chain = (
            #     RunnablePassthrough.assign(context=(lambda x: x["question"]) | tavily_tool)
            #     | doc_search_prompt
            #     | llm
            #     | StrOutputParser()
            # )
            chain = (
                doc_search_prompt
                | llm
                | StrOutputParser()
            )
            response = chain.stream({"languageSelect":self.languageSelect,"question": self.query})
            # for chunk in response:
            #     # 输出逐步生成的文本块
            #     sys.stdout.write(chunk)
            #     sys.stdout.flush()
            return response
        except Exception as e:
            self.app.logger.debug(e)
            return {
                "_action": "tavily search",
                "success": False,
                "error": f"an error occurred {str(e)}",
            }

 

# if __name__ == '__main__':
#     webs = tavily_search('mistral-nemo:12b','what is index')
#     webs.web_search()