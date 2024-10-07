from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import os

class tavily_search:
    def __init__(self,llm_model: any = None,query: str = None,model_type: str = None):
        self.llm_model = llm_model
        self.query = query
        self.model_type = model_type
        if self.model_type == 'openai':
            self.chatbot =  ChatOpenAI(model=self.llm_model, temperature=0,openai_api_base = os.getenv("OPENAI_API_BASE"),streaming=True)
        elif self.model_type == 'kimi':
            self.chatbot = ChatOpenAI(model=self.llm_model, temperature=0,api_key=os.getenv("KIMI_API_KEY"),openai_api_base = os.getenv("KIMI_API_BASE"),streaming=True)
        else:
            self.chatbot = ChatOllama(model=self.llm_model,max_tokens=8192, temperature=0.8)

    def web_search(self):
        try:
            tavily_tool = TavilySearchResults(max_results=2,search_depth="advanced")
            # doc_search_prompt =ChatPromptTemplate.from_template("""
            #                 according to question, Search only in oracle official documentation web site https://docs.oracle.com or https://blogs.oracle.com and database type only is oracle database,then search releated document
            #                 Question: {question}
            #                 """)
            doc_search_prompt =ChatPromptTemplate.from_template("""
                            Question: {question}
                            """)
            # llm = ChatOllama(
            #     model=self.llm_model,
            #     temperature=0,
            # )
            # 将生成的查询传递给最终答案的提交工具
            

            chain = (
                RunnablePassthrough.assign(context=(lambda x: x["question"]) | tavily_tool)
                | doc_search_prompt
                | self.chatbot
                | StrOutputParser()
            )
            # chain = (
            #     doc_search_prompt
            #     | llm
            #     | StrOutputParser()
            # )
            response = chain.stream({"question": self.query})
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