import re
from datetime import date

from langchain_core.tools import tool

conn = None


def get_connection():
    """获取数据库连接对象"""
    import pymysql

    global conn
    if conn is None or not conn.open:
        try:
            conn = pymysql.connect(
                host='192.168.31.175',
                port=3306,
                user='jhyl**hr',
                password='JHyl*#369',
                database='wj2',
            )
            print('数据库连接成功')
        except pymysql.MySQLError as e:
            raise Exception(f'数据库连接失败: {e}') from e
    return conn


@tool
def sql_outage(sql: str) -> str:
    """生成关于停电信息的sql查询语句。表结构：TABLE( \
        t_event_alarm_inter (equipName 设备名称,lineName 线路名称,faultType 停电类型,\
        occurTime 停电开始时间,endTime 停电结束时间,
        gdsName 供电所名称，unitName 供电公司名称)。"""
    sql = sql.replace('`', '').replace('\\n', ' ')
    search = re.search(r'((select|SELECT)[^"]+)', sql)
    if search:
        sql = search.group()
        if ' * ' in sql:
            sql = sql.replace(
                '*',
                'equipName as 设备名称, lineName as 线路名称, faultType as 停电类型, occurTime as 停电开始时间, \
                    endTime as 停电结束时间, gdsName as 供电所名称, unitName as 供电公司名称',
            )
        return sql
    return ''


@tool
def sql_order_fault(sql: str) -> str:
    """生成关于工单故障的sql查询语句。只输出给定字段，用as替代表名。表结构为 TABLE t_fault_order_inter (
    work_order_id 工单号, received_time 受理时间,  address  地址,
    issue_description  受理内容,phone_number 联系电话,contact_person 联系人,
    analysis_result 分析结果, order_type 工单类型, unit_name 单位,
    power_supply_station 供电所）。"""
    sql = sql.replace('`', '').replace('\\n', ' ')
    search = re.search(r'((select|SELECT)[^"]+)', sql)
    if search:
        sql = search.group()
        if ' * ' in sql:
            sql = sql.replace(
                '*', 'work_order_id as 工单号, received_time as 受理时间, address as 地址,contact_person as 联系人'
            )
        return sql
    return ''


@tool
def extract_args(line_name: str, fault_type: str, unit_name: str, occur_time: date, end_time: date) -> str:
    """线路和时间的停电查询。获取用户提问，填充sql查询语句的select字段和where条件字段。"""
    base_query = 'select * from t_event_alarm_inter where 1=1'
    if line_name:
        base_query += f" and lineName LIKE '{line_name}%'"
    if fault_type:
        base_query += f" and faultType LIKE '{fault_type}%'"
    if unit_name:
        base_query += f" and unitName LIKE '{unit_name}%'"
    if occur_time:
        base_query += f" and occurTime>='{occur_time}'"
    if end_time:
        base_query += f" and (endTime<='{end_time}' or endTime is null)"
    return base_query
