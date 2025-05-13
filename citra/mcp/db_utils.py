import pymysql

# 全局连接和游标对象
conn = None
cursor = None


def get_connection():
    """获取数据库连接对象"""
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
            print(f'数据库连接失败: {e}')
            raise
    return conn


# def close_connection():
#     """关闭数据库连接"""
#     global conn, cursor
#     if cursor:
#         cursor.close()
#         cursor = None
#     if conn and conn.open:
#         conn.close()
#         conn = None
