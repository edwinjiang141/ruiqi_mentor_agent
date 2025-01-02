import streamlit as st
def main():
    st.set_page_config(
       page_title="Oracle智能知识库",
       layout="wide",
       initial_sidebar_state="expanded"
    )
    with st.sidebar:
         st.image('../client/img/23ai.png', width=200)
         st.title("Oracle智能知识库")

         admin_page = st.Page("document_loader.py",
                              title="向量库管理", icon=":material/handyman:")
         client_page = st.Page("vector_search.py", title="向量库检索", icon=":material/search:")
         database_page = st.Page("vector_database.py", title="向量数据库", icon=":material/database:")
    choosed_page = st.navigation([client_page, admin_page, database_page])
    choosed_page.run()
    
if __name__ == "__main__":
    main()