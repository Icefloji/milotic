# %%
import datetime
from typing import Annotated, Literal

import pandas as pd
import pymysql
from langchain_community.chat_models import ChatTongyi  #  noqa: F401
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_ollama.chat_models import ChatOllama  #  noqa: F401
from typing_extensions import TypedDict

from citra.mcp.tool import get_connection, sql_outage

conn = get_connection()


# %%
model = ChatTongyi(model='qwen-max', temperature=0.7)
# model = ChatOllama(model='qwen3:8b', temperature=0.7)
tools = [sql_outage]

chat_with_tools = model.bind_tools(tools)

# %%


class QueryFormat(TypedDict):
    format: Annotated[Literal['excel', 'image', 'markdown'], '判断查询返回的格式。默认为markdown，可选excel,image']  # noqa: E501


model_with_format = model.with_structured_output(QueryFormat)


# %%
def call_tools(ai_msg: AIMessage) -> ToolMessage:
    """Simple sequential tool calling helper."""
    tool_map = {tool.name: tool for tool in tools}
    select_tool = tool_map[ai_msg.tool_calls[0]['name']]
    tool_msg = select_tool.invoke(ai_msg.tool_calls[0])
    return tool_msg


def str_to_gen(s: str, *, msg_type: str = 'msg', chunk_size: int = 10):
    """将字符串转换为生成器"""
    for i in range(0, len(s), chunk_size):
        yield {'type': msg_type, 'content': s[i : i + chunk_size]}


def execute_sql(sql: str):
    """执行sql语句"""
    with conn.cursor() as cursor:
        try:
            cursor.execute(sql)
        except pymysql.err.ProgrammingError as e:
            raise ValueError('查询过程出错，请重试') from e
        results = cursor.fetchall()
        cols = [desc[0] for desc in cursor.description]
        # cols = [col_dict.get(c,c) for c in cols]
        df = pd.DataFrame(results, columns=cols)
        df.fillna('', inplace=True)
    return df


def consult_database(question: str):
    """根据问题生成sql查询语句，然后执行查询并返回结果，并修改为不同的格式"""

    now = datetime.date.today()
    question = f'今天是{str(now)},{question}'
    messages: list[BaseMessage] = [HumanMessage(content=question)]
    ai_msg = chat_with_tools.invoke(question)
    if not ai_msg.tool_calls:  # type: ignore
        print('没有调用工具')
        yield from str_to_gen(ai_msg.content, chunk_size=5)  # type: ignore
    else:
        print('调用工具')
        import uuid

        query: str = call_tools(ai_msg).content  # type: ignore
        print(query)
        df_res = execute_sql(query)
        if df_res.size == 0:
            yield {'type': 'msg', 'content': '没有查询到数据,请补充问题'}
            return
        # 根据返回的结果类型，返回不同的格式
        # messages.append(AIMessage(content=df_res.to_string(index=False)[:100]))
        # yield from model.stream([SystemMessage('根据用户问题，和数据库查询结果，生成数据描述')] + messages)
        return_type = model_with_format.invoke(question)
        if return_type is None:
            return_type = 'markdown'
        else:
            return_type = return_type['format']
        print(return_type)
        if return_type == 'markdown':
            yield {'type': 'markdown', 'content': df_res.to_markdown(index=False)}
        elif return_type == 'excel':
            tab_name = uuid.uuid4().hex
            df_res.to_excel(f'citra/service/cache/{tab_name}.xlsx', index=False)
            yield {'type': 'excel', 'content': f'/cache/{tab_name}.xlsx'}
        elif return_type == 'image':
            import dataframe_image as dfi

            df_name = uuid.uuid4().hex
            dfi.export(df_res, f'citra/service/cache/{df_name}.png')
            yield {'type': 'image', 'content': f'/cache/{df_name}.png'}
