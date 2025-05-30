# ruff:noqa: E501
def get_safety(safe_list: list[dict], code: str):
    # 工作票1。根据安全措施类型代码获取安全措施列表
    filter_list = [item for item in safe_list if item['conOfSecurityMeasuresTypeCode'] == code]
    return sorted(filter_list, key=lambda x: x['lineNo'])


def get_person_change(person_list: list[dict]):
    # 配电施工。获取新增人员
    filter_list = [item for item in person_list if item['addStaffSign'] != '']
    return sorted(filter_list, key=lambda x: x['addStaffSignTime'])


newline = '\n'


# %%
def get_ticket1(tk: dict) -> str:
    return f"""
    单位：{tk['SGDistributionFirstWorkTicket'][0]['workUnit']}
    编号：{tk['SGDistributionFirstWorkTicket'][0]['workTicketCode']}

    1.工作负责人：{tk['SGDistributionFirstWorkTicket'][0]['workingControllerName']}
    班组：{tk['SGDistributionFirstWorkTicket'][0]['workingClassName']}

    2.工作班成员(不包括工作负责人)：
    {tk['SGDistributionFirstWorkTicket'][0]['workingPerson'].split('|')[0]}   共{len(tk['SGDistributionFirstWorkTicket'][0]['workingPerson'].split('|')[1].split(','))}人。

    3.停电线路名称(多回线路应注明双重称号)：{tk['SGDistributionFirstWorkTicket'][0]['lineName']}

    4.工作任务：
    |工作地点(地段)或设备|  工作内容|
    |-------------------------------|--------------|
    {newline.join([f'|{x["workPlace"]}|{x["workContent"]}|' for x in tk['SGTaskList']])}

    5.计划工作时间：自{tk['SGDistributionFirstWorkTicket'][0]['scheduledStartTime']}至 {tk['SGDistributionFirstWorkTicket'][0]['plannedEndTime']}

    6.安全措施(应改为检修状态的线路、设备名称，应断开的断路器（开关）、隔离开关（刀闸）、熔断
    器，应合上的接地刀闸，应装设的接地线、绝缘隔板、遮栏（围栏）和标识牌等，装设的接地线应明确具体位置，必要时可附页绘图说明)：

    6.1 调控或运维人员[变配电站、发电厂等]应采取的安全措施
    |安全措施 |接地线编号|已执行|
    |--------|----|--------|
    {newline.join([f'|{x["contentOfSecurityMeasures"]}|{x["groundWireCode"]}|{"√" * int(x["isExecutionCode"])}|' for x in get_safety(tk['SGSafetyMeasures'], 'ControlPersonnelMeasures')])}

    6.2 工作班完成的安全措施
    |安全措施|已执行|
    |-------|-----|
    {newline.join([f'|{x["contentOfSecurityMeasures"]}| {"√" * int(x["isExecutionCode"])}|' for x in get_safety(tk['SGSafetyMeasures'], 'WorkingClassMeasures')])}

    6.3工作班装设(或拆除)的接地线
    |线路名称、设备双重名称、装设位置|接地线编号|装设人|装设时间|拆除人|拆除时间|
    |-------------------------------------|-----------|-------|----------|------|---------|
    {newline.join([f'|{x["contentOfSecurityMeasures"]}|{"√" * int(x["isExecutionCode"])}|' for x in get_safety(tk['SGSafetyMeasures'], 'ShutdownPowerLine')])}

    6.4  配合停电线路应采取的安全措施
    | 安全措施 | 接地线编号| 已执行   |
    |---|---|----|
    {newline.join([f'|{x["contentOfSecurityMeasures"]}| {"√" * int(x["isExecutionCode"])}|' for x in get_safety(tk['SGSafetyMeasures'], 'AdditionalMeasures')])}

    6.5保留或邻近的带电线路、设备：
    {get_safety(tk['SGSafetyMeasures'], 'WithPowerLine')[0]['contentOfSecurityMeasures']}

    6.6其它安全措施和注意事项：
    {get_safety(tk['SGSafetyMeasures'], 'MattersNeedingAttention')[0]['contentOfSecurityMeasures']}
    """


# %%
def get_ticket2(tk: dict) -> str:
    return f"""
    单位 ：{tk['SGDistributionSecondWorkticket'][0]['workUnit']} 编号：{tk['SGDistributionSecondWorkticket'][0]['workTicketCode']}
    1 工作负责人（监护人）{tk['SGDistributionSecondWorkticket'][0]['workingControllerName']} 班组：{tk['SGDistributionSecondWorkticket'][0]['workingControllerTeam']}

    2 工作班人员（不包括工作负责人）：
    {tk['SGDistributionSecondWorkticket'][0]['workingPerson']}  共{tk['SGDistributionSecondWorkticket'][0]['number']}人

    3 工作任务
    |工作地点(地段)或设备|  工作内容|
    |-------------------------------|--------------|
    {newline.join([f'|{x["workPlace"]}|{x["workContent"]}|' for x in tk['SGTaskList']])}

    4 计划工作时间：自{tk['SGDistributionSecondWorkticket'][0]['scheduledStartTime']}至 {tk['SGDistributionSecondWorkticket'][0]['plannedEndTime']}
    """


def get_breakfix(tk: dict) -> str:
    return f"""
    单位 ：{tk['SGEmergencyRepairWorkticket'][0]['Unit']} 票号：{tk['SGEmergencyRepairWorkticket'][0]['workTicketCode']}
    1 抢修工作负责人：{tk['SGEmergencyRepairWorkticket'][0]['workingControllerName']} 班组：{tk['SGEmergencyRepairWorkticket'][0]['workingControllerTeam']}
    风险等级：{tk['SGEmergencyRepairWorkticket'][0]['riskLevel']}

    2 抢修班人员（不包括抢修工作负责人）：
    {tk['SGEmergencyRepairWorkticket'][0]['workingPerson']} 共{tk['SGEmergencyRepairWorkticket'][0]['number']}人

    3 抢修工作任务
    |工作地点(地段)或设备|  工作内容|
    |-------------------------------|--------------|
    {newline.join([f'|{x["workPlace"]}|{x["workContent"]}|' for x in tk['SGTaskList']])}
"""


# %%
def get_ticket(ticket_type: str, json_tk: dict) -> str:
    instance = ''
    if ticket_type == 'ticket1':
        instance = get_ticket1(json_tk)
    elif ticket_type == 'ticket2':
        instance = get_ticket2(json_tk)
    elif ticket_type == 'breakfix':
        instance = get_breakfix(json_tk)
    return instance
