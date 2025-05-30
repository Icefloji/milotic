import json

from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_ollama import ChatOllama

model = ChatOllama(model='qwen2.5:3b', temperature=0.7)

# %%
store = {}


def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]


with_message_history = RunnableWithMessageHistory(model, get_session_history)

config = {'configurable': {'session_id': 'abc2'}}


def talk(message: str, id: str = 'abc2'):
    config = {'configurable': {'session_id': id}}
    output = with_message_history.stream(message, config=config)
    for i in output:
        yield {'type': 'msg', 'content': i.content}


if __name__ == '__main__':
    for i in talk('你好'):
        print(json.loads(i)['content'], end='')
