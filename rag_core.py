import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# 加载 .env 配置
load_dotenv()

# 加载 PDF 并按规则切分成小块
def load_and_split_pdf(pdf_path):
    loader = PyPDFLoader(pdf_path)
    pages = loader.load_and_split()
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    
    chunks = text_splitter.split_documents(pages)
    return chunks

# 把切分好的文本块向量化，存入 Chroma 数据库
def build_vectorstore(chunks, persist_dir="./chroma_db"):
    # 使用中文嵌入模型 BAAI/bge-small-zh-v1.5，维度 512
    embeddings = HuggingFaceBgeEmbeddings(model_name="BAAI/bge-small-zh-v1.5")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_dir
    )
    return vectorstore

# 获取已有的向量数据库
def get_vectorstore(persist_dir="./chroma_db"):
    embeddings = HuggingFaceBgeEmbeddings(model_name="BAAI/bge-small-zh-v1.5")
    return Chroma(
        persist_directory=persist_dir,
        embedding_function=embeddings
    )

# 构建 RAG 问答链
def build_rag_chain(vectorstore):
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    
    llm = ChatOpenAI(
        model=os.getenv("LLM_MODEL", "deepseek-v4-flash"),  # 默认用新模型名
        base_url=os.getenv("OPENAI_BASE_URL"),
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0.1
    )
    
    template = """你是一个知识库问答助手，严格根据以下上下文回答问题。
如果文档中没有相关信息，请如实告知“文档中没有找到相关内容。”
上下文：
{context}

问题：
{question}
"""
    prompt = PromptTemplate.from_template(template)
    
    def format_docs(docs):
        # 处理可能的嵌套列表：如果 docs 是 [[Document, ...]]，则展平
        if docs and isinstance(docs[0], list):
            docs = docs[0]
        return "\n\n".join(doc.page_content for doc in docs)
    
    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain, retriever

# 对外接口：索引 PDF，返回切分数量
def index_pdf(pdf_path):
    chunks = load_and_split_pdf(pdf_path)
    build_vectorstore(chunks)
    return len(chunks)

# 对外接口：提问，返回答案和来源
def ask_question(question, vectorstore):
    chain, retriever = build_rag_chain(vectorstore)
    answer = chain.invoke(question)
    
    # 检索文档并展平
    docs = retriever.invoke(question)
    if docs and isinstance(docs[0], list):
        docs = docs[0]
    
    sources = list(set(doc.metadata.get("source", "") for doc in docs))
    return answer, sources