# %%
import datetime
from datetime import date

from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool

# %%
from citra.mcp.db_utils import get_connection

conn = get_connection()


# %%
@tool
def count_outage_by_line(line_name: str, start_time: date, end_time: date) -> str:
    """线路停电次数查询。获取某条线路(line_name)在过去一段时间（start_time，end_time）内的故障次数，如果地点不是某线路，那么查询所有记录"""
    # cursor.execute(f'select count(*)  from t_event_alarm_inter where lineName={line_name} LIMIT 1')
    # if cursor.fetchone() is None:
    # return f'线路{line_name}不存在，请检查线路名称'
    global cursor
    query = f"select   COUNT(*) as outage_time from t_event_alarm_inter where lineName='{line_name}' and occurTime>='{start_time}' and endTime<='{end_time}'"
    with conn.cursor() as cursor:
        cursor.execute(query)
        count = cursor.fetchall()[0][0]
    return f'{line_name}在{start_time}到{end_time}间的停电次数为：{count}'


@tool
def count_outage_today(unit_name: str) -> str:
    """当天停电次数查询。获取某个单位（unit_name）在今天的停电次数"""
    global cursor
    today = datetime.date.today().strftime('%Y-%m-%d')
    query = f"select  COUNT(*) as outage_time from t_event_alarm_inter where unitName LIKE'{unit_name}%' and occurTime>='{today}' "
    with conn.cursor() as cursor:
        cursor.execute(query)
        count = cursor.fetchall()[0][0]
    return f'{unit_name}今天的停电次数为：{count}'


@tool
def inspect_outage(unit_name: str) -> str:
    """当天停电次数查询。获取某个单位（unit_name）在今天的停电次数"""
    global cursor
    today = datetime.date.today().strftime('%Y-%m-%d')
    query = f"select *  from t_event_alarm_inter where unitName LIKE'{unit_name}%' and occurTime>='{today}' "
    with conn.cursor() as cursor:
        cursor.execute(query)
        count = cursor.fetchall()[0][0]
    return f'今天的停电为：{count}'


chatllm = ChatTongyi(model='qwen-max')
tools = [count_outage_by_line, count_outage_today]
chat_with_tools = chatllm.bind_tools(tools)


def call_tools(msg: AIMessage) -> list[dict]:
    """Simple sequential tool calling helper."""
    tool_map = {tool.name: tool for tool in tools}
    tool_calls = msg.tool_calls.copy()
    for tool_call in tool_calls:
        tool_call['output'] = tool_map[tool_call['name']].invoke(tool_call['args'])
    return tool_calls


chain = chat_with_tools | call_tools


# %%


# %%
def ask_outage(question: str) -> str:
    """Ask a question to the model and get the answer."""
    now = datetime.date.today().strftime('%Y-%m-%d')
    answer = chat_with_tools.invoke([HumanMessage(content=f'今天日期是{now},{question}')])
    result = call_tools(answer)
    return result[0]['output']


# %%
