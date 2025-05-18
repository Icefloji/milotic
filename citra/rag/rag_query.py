# %%

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_ollama import ChatOllama

# %%
model = ChatOllama(model='qwen2.5:3b')
template = (
    '你是供电局的客服，请根据知识库，回答用户的问题，并列出引用自第几条 和第几点。问题：{question}。知识库：{docs}。'
)
prompt = PromptTemplate(template=template, input_variables=['question', 'docs'])
rag_chain = prompt | model | StrOutputParser()


def load_retriever():
    # 自定义的文本拆分器
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=30, separators=['第'])
    loader = TextLoader('data/rag/extracted_text.txt', encoding='utf-8')
    docs = loader.load_and_split(text_splitter=text_splitter)
    vectorstore = Chroma.from_documents(documents=docs, embedding=DashScopeEmbeddings(model='text-embedding-v3'))
    retriever = vectorstore.as_retriever(search_type='similarity', search_kwargs={'k': 3})
    return retriever


# %%
def format_docs(docs):
    return '\n\n'.join(doc.page_content for doc in docs)


def ask_rag(retriever, question):
    formatted_docs = (retriever | format_docs).invoke(question)
    yield 'event: start\ndata: {}\n\n'
    for chuck in rag_chain.stream({'question': question, 'docs': formatted_docs}):
        yield f'event: message\ndata: {chuck}\n\n'
    yield 'event: end\ndata: {end}\n\n'
