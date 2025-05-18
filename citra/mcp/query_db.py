import json
from typing import Any

from langchain_community.chat_models import ChatTongyi  # noqa:F401
from langchain_core.messages import AIMessage, HumanMessage
from langchain_ollama.chat_models import ChatOllama

from citra.mcp.tool import get_connection, sql_order_fault, sql_outage

conn = get_connection()


# %%
def to_markdown(cols: list, rows: tuple[tuple[Any, ...], ...]):
    if len(cols) != len(rows[0]):
        raise ValueError('列数和行数不匹配')
    headers = '| ' + ' | '.join(cols) + ' |\\n'
    seps = '| ' + ' | '.join(['---'] * len(cols)) + ' |\\n'
    yield json.dumps({'type': 'table', 'content': headers}, ensure_ascii=False)
    yield json.dumps({'type': 'table', 'content': seps}, ensure_ascii=False)
    for row in rows:
        r = '| ' + ' | '.join(str(cell) for cell in row) + ' |\\n'
        yield json.dumps({'type': 'table', 'content': r}, ensure_ascii=False)


def str_to_gen(s: str, *, msg_type: str = 'msg', chunk_size: int = 10):
    """将字符串转换为生成器"""
    for i in range(0, len(s), chunk_size):
        yield json.dumps({'type': 'msg', 'content': s[i : i + chunk_size]}, ensure_ascii=False)


def execute_sql(sql: str):
    """执行sql语句，返回结果"""

    if sql == '':
        return '生成sql失败'
    with conn.cursor() as cursor:
        try:
            cursor.execute(sql)
            results = cursor.fetchall()
            if not results:
                yield json.dumps({'type': 'err', 'content': '没有查询到数据'}, ensure_ascii=False)
                return
            cols = [desc[0] for desc in cursor.description]
            yield from to_markdown(cols, results)
        except Exception:
            yield json.dumps({'type': 'err', 'content': '查询出错'}, ensure_ascii=False)


# %%
# chatllm = ChatTongyi(model='qwen-max', temperature=0.7)
try:
    chatllm = ChatOllama(model='qwen2.5:3b', temperature=0.7)
except Exception as e:
    raise Exception('服务未启动') from e
tools = [sql_outage, sql_order_fault]

chat_with_tools = chatllm.bind_tools(tools)


def call_tools(msg: AIMessage):
    """Simple sequential tool calling helper."""
    tool_map = {t.name: t for t in tools}
    tool_calls = msg.tool_calls.copy()
    for tool_call in tool_calls:
        tool_call['output'] = tool_map[tool_call['name']].invoke(tool_call['args'])  # type: ignore
    return tool_calls


def ask_question(question: str):
    """问数据库问题"""
    try:
        from datetime import date

        now = date.today()
        question = f'今天是{str(now)}，{question}'
        ai_msg = chat_with_tools.invoke([HumanMessage(content=question)])
        if not ai_msg.tool_calls:  # type: ignore
            print('没有调用工具')
            yield from str_to_gen(ai_msg.content)  # type: ignore
        else:
            print('调用工具')
            query = call_tools(ai_msg)[0]['output']  # type: ignore
            print(query)
            yield from execute_sql(query)
    except Exception as e:
        print(f'遇到错误: {e}')


if __name__ == '__main__':
    for i in ask_question('江山供电公司这个月的故障信息'):
        print(i, end='')
