import json
from pathlib import Path

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.chat_models import ChatTongyi  # noqa: F401
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_ollama import OllamaEmbeddings

text_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20, separators=['第'])

vectorstore = Chroma(persist_directory='data/rag/knowledge_base', embedding_function=OllamaEmbeddings(model='bge-m3:latest'))
retriever = vectorstore.as_retriever(search_type='similarity', search_kwargs={'k': 3})

examples = [
    {
        'question': '用户单相用电设备总容量 12 千瓦以下时，可以采用多少供电？',
        'doc': '《供电营业规则》',
        'articles': '第九条',
        'answer': '当用户单相用电设备总容量为12千瓦以下时，可以采用低压220伏的供电方式。',
        'link': 'http://192.168.31.147:8000/knowledge_base/1.pdf',
    },
    {
        'question': '申请非永久性减容的，时长是多久？',
        'doc': '《供电营业规则》',
        'articles': '第二十五条',
        'answer': '申请非永久性减容的，减容次数不受限制，每次减容时长不得少于十五日，最长不得超过两年。',
        'link': 'http://192.168.31.147:8000/knowledge_base/2.pdf',
    },
    {
        'question': '用户集资建设的供电站，建成运营前，由谁管理？',
        'doc': '《供电营业规则》',
        'articles': '第四十九条',
        'answer': '用户集资建设的供电设施建成后，其运行维护管理按照以下规定确定：（一）属于公用性质或占用公用线路规划走廊的，由供电企业统一管理。',
        'link': 'http://192.168.31.147:8000/knowledge_base/3.pdf',
    },
]
example_prompt = ChatPromptTemplate(
    [
        ('human', '{question}'),
        ('ai', '根据{doc}，{articles}。{answer}[《供电营业规则》]({link})'),
    ]
)

few_shot_promppt = FewShotChatMessagePromptTemplate(
    example_prompt=example_prompt,
    examples=examples,
)

final_prompt = ChatPromptTemplate(
    [
        ('system', '根据供电局知识库，严格模仿以下例子，回答用户的问题。'),
        few_shot_promppt,
        ('human', '问题：{question}'),
        ('ai', 'json格式知识库：。{docs}'),
    ]
)


service_ip = '127.0.0.1:8000/'


def format_docs(docs):
    doc_res = []
    for doc in docs:
        d = {}
        d['name'] = Path(doc.metadata['source']).stem
        d['link'] = service_ip + str(Path('knowledge_base', Path(doc.metadata['source']).stem).with_suffix('.pdf').as_posix())
        d['content'] = doc.page_content
        doc_res.append(json.dumps(d, ensure_ascii=False))
    return '\n\n'.join(doc_res)


model = ChatTongyi(model='qwen-max')
# model2 = ChatOllama(model='qwen2.5:3b')
rag_chain = RunnableParallel(question=RunnablePassthrough(), docs=retriever | format_docs) | final_prompt | model | StrOutputParser()


def query_knowledge_base(ip, question):
    global service_ip
    service_ip = ip
    for i in rag_chain.stream(question):
        yield {'type': 'markdown', 'content': i}


if __name__ == '__main__':
    print(rag_chain.invoke('申请非永久性减容的，时长是多久？'))
