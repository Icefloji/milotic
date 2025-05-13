from langchain_core.tools import tool


@tool
def count_outage(line_name: str, start_time: date, end_time: date) -> str:
    """停电次数查询。获取某条线路(line_name)在过去一段时间（start_time，end_time）内的故障次数"""
    query = f"select   COUNT(*) as outage_time from t_event_alarm_inter where lineName='{line_name}' and occurTime>='{start_time}' and endTime<='{end_time}'"
    cursor.execute(query)
    count = cursor.fetchall()[0][0]
    res_str = f'{line_name}在{start_time}到{end_time}间的停电次数为：{count}'
    return res_str
