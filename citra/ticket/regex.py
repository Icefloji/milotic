# %%
import re
from typing import List


# %%
def re_work_person(names: str = '傅东根,李强,李林,徐贵强,彭祝化等', count: int = 8) -> dict:
    explain = suggestion = ''
    names = names.strip().replace('，', ',')
    flag_deng: int = 0
    if names[-1] == '等':
        names = names[:-1]
        flag_deng = 1
    name_conut = names.count(',') + (0 if names[-1] == ',' else 1)
    if count <= 5:
        if count != name_conut:
            explain += '签名数量和工作班人数不一致。'
            suggestion += '检查工作班人数。'
        if flag_deng == 1:
            explain += '末尾多加‘等’字。'
            suggestion += '末尾删除‘等’字。'
    else:
        if name_conut != 5:
            explain += '签名人数不为5。'
            suggestion += '检查签名数量。'
        if flag_deng == 0:
            explain += '缺少‘等’字。'
            suggestion += '末尾加上‘等’字。'
    if explain != '':
        return {
            'node': '2. 工作班成员',
            'satisfied': '0',
            'rule': '1',
            'explain': explain,
            'suggestion': suggestion,
        }
    return {}


def re_outage_line(
    line: str = '10kV里金555线93号杆大号侧线路至芦四坑支线1号杆开关进线侧线路。',
) -> dict:
    explain = suggestion = ''
    match = re.search(r'(\d+([Kk][vV]))?(([\u4e00-\u9fff]+)?(\d+)?线)?', line)
    if match:
        voltage, kv, line, site, number = (
            match.group(1),
            match.group(2),
            match.group(3),
            match.group(4),
            match.group(5),
        )
        if voltage:
            if kv != 'kV':
                explain += '电压单位不正确。'
                suggestion += '修改单位为kV。'
        else:
            explain += '缺少电压等级。'
            suggestion += '补充电压等级。'
        if line:
            if site is None:
                explain += '线路名称缺少地点。'
                suggestion += '补充地点。'
            if number is None:
                explain += '线路名称缺少数字。'
                suggestion += '补充数字 。'
        else:
            explain += '缺少线路名称。'
            suggestion += '补充线路名称。'
    if explain != '':
        return {
            'node': '3.停电线路名称',
            'satisfied': '0',
            'rule': '2',
            'explain': explain,
            'suggestion': suggestion,
        }
    return {}


def re_work_site(sites: List[str]) -> dict:
    if sites is None:
        sites = ['10kV里金线96+1号杆至芹溪村2号变支线2号杆。']
    explain = suggestion = ''
    for idx, site in enumerate(sites):
        match = re.search(r'(\d+([Kk][vV]))?(([\u4e00-\u9fff]+)?(\d+)?线)?([+\d]+号?杆)?', site)
        if match:
            voltage, kv, line, site, number, pole = (
                match.group(1),
                match.group(2),
                match.group(3),
                match.group(4),
                match.group(5),
                match.group(6),
            )
            if voltage:
                if kv != 'kV':
                    explain += f'行{idx}:电压单位不正确。'
                    suggestion += f'行{idx}:修改单位为kV。'
            else:
                explain += f'行{idx}:缺少电压等级。'
                suggestion += f'行{idx}:补充电压等级。'
            if line:
                if site is None:
                    explain += f'行{idx}:线路名称缺少地点。'
                    suggestion += f'行{idx}:补充地点。'
                if number is None:
                    explain += f'行{idx}:线路名称缺少数字。'
                    suggestion += f'行{idx}:补充数字 。'
            else:
                explain += f'行{idx}:缺少线路名称。'
                suggestion += f'行{idx}:补充线路名称。'
            if pole is None:
                explain += f'行{idx}:缺少杆号。'
                suggestion += f'行{idx}:补充具体杆号。'
    if explain != '':
        return {
            'node': '4.工作任务',
            'satisfied': '0',
            'rule': '3',
            'explain': explain,
            'suggestion': suggestion,
        }
    return {}


def re_plan_time(start_time: str = '2025-04-03 08:00:00', end_time: str = '2025-04-02 16:00:00') -> dict:
    # 计划工作时间
    from datetime import datetime

    start = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
    end = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
    if start > end:
        return {
            'node': '5.计划工作时间',
            'satisfied': '0',
            'rule': '4',
            'explain': '工作开始时间晚于结束时间。',
            'suggestion': '检查起始时间的正确性。',
        }
    elif (end - start).days > 1:
        return {
            'node': '5.计划工作时间',
            'satisfied': '0',
            'rule': '4',
            'explain': '工作时间超过一天。',
            'suggestion': '检查工作时长。',
        }
    else:
        return {}


# %%
def rec_re_ticket1(tk: dict) -> List[dict[str, str]]:
    """
    根据正则表达式判断工作票规范性
    func，识别某个栏的函数，args 输入参数名称
    | func          |  arg1              |          arg2          |arg3   |
    |re_work_person | 名字               | 人数                    |
    |re_outage_line |停电线路名称         |
    |re_work_site   |工作地点(列表)       |
    |re_plan_time   |开始时间            | 结束时间                         |
    """

    # fmt: off
    results = []
    results.append(re_work_person(tk['SGDistributionFirstWorkTicket'][0]['workingPerson'].split('|')[0], len(tk['SGDistributionFirstWorkTicket'][0]['workingPerson'].split('|')[1].split(','))))
    results.append(re_outage_line(tk['SGDistributionFirstWorkTicket'][0]['lineName']))
    results.append(re_work_site([x['workPlace'] for x in tk['SGTaskList']]))
    results.append(re_plan_time(
            tk['SGDistributionFirstWorkTicket'][0]['scheduledStartTime'],
            tk['SGDistributionFirstWorkTicket'][0]['plannedEndTime'],
        )
    )
    # fmt: on
    results = list(filter(None, results))
    return results


# %%
def rec_re_ticket2(tk: dict) -> List[dict[str, str]]:
    results = []
    # fmt: off
    results.append(re_work_person(tk["SGDistributionSecondWorkticket"][0]["workingPerson"],tk["SGDistributionSecondWorkticket"][0]["number"]))
    results.append(re_work_site([x['workPlace'] for x in tk["SGTaskList"]]))
    results.append(re_plan_time(tk["SGDistributionSecondWorkticket"][0]["scheduledStartTime"],tk["SGDistributionSecondWorkticket"][0]["plannedEndTime"]))
    # fmt: on
    results = list(filter(None, results))
    return results


# %%
def rec_re_breakfix(tk: dict) -> List[dict[str, str]]:
    results = []
    # fmt: off
    results.append(re_work_person(tk["SGEmergencyRepairWorkticket"][0]["workingPerson"],len(tk["SGEmergencyRepairWorkticket"][0]["workingPerson"].split(','))))
    results.append(re_work_site([x['workPlace'] for x in tk["SGTaskList"]]))
    # fmt: on
    results = list(filter(None, results))
    return results


# %%
def rec_re_electric1(tk: dict) -> List[dict[str, str]]:
    results = []
    # fmt: off
    results.append(re_work_person(tk["SGEmergencyRepairWorkticket"][0]["workingPerson"],len(tk["SGEmergencyRepairWorkticket"][0]["workingPerson"].split(','))))
    results.append(re_work_site([x['workPlace'] for x in tk["SGTaskList"]]))
    # fmt: on
    results = list(filter(None, results))
    return []


# %%
def rec_re_electric2(tk: dict) -> List[dict[str, str]]:
    results = []
    # fmt: off
    results.append(re_work_person(tk["SGEmergencyRepairWorkticket"][0]["workingPerson"],len(tk["SGEmergencyRepairWorkticket"][0]["workingPerson"].split(','))))
    results.append(re_work_site([x['workPlace'] for x in tk["SGTaskList"]]))
    # fmt: on
    results = list(filter(None, results))
    return []
