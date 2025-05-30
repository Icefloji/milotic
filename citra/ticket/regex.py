import re
from datetime import datetime
from typing import Dict, List


def re_work_person(names: str, count: int) -> Dict:
    """识别工作班成员"""
    explain = suggestion = ''
    names = names.replace('，', ',').replace(' ', '')
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
            'node': '2.工作班成员',
            'satisfied': '0',
            'rule': '1',
            'explain': explain,
            'suggestion': suggestion,
        }
    return {}


def re_outage_line(line: str) -> Dict:
    """识别停电线路"""
    explain = suggestion = ''
    match = re.match(r'(\d+(kv|kV|KV|千伏))?([\u4e00-\u9fff]+([A-Za-z\d]+)[\u4e00-\u9fff]*线)?', line)
    if match:
        voltage, kv, line, number = (
            match.group(1),
            match.group(2),
            match.group(3),
            match.group(4),
        )
        if voltage:
            if kv != 'kV':
                explain += '电压单位不正确。'
                suggestion += '修改单位为kV。'
        else:
            explain += '缺少电压等级。'
            suggestion += '补充电压等级。'
        if line:
            if number is None:
                explain += '线路缺少设备名称。'
                suggestion += '补充设备名称。'
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


def re_work_site(sites: List[str]) -> Dict:
    """识别工作地点"""
    explain = suggestion = ''
    for idx, site in enumerate(sites):
        idx = idx + 1
        if '杆' in site:
            site = site.split('杆')[0] + '杆'
        elif '线' in site:
            site = site.split('线')[0] + '线'
        match = re.match(
            r'(\d+(kv|kV|KV|千伏))?([\u4e00-\u9fff]+([A-Za-z\d]+)[\u4e00-\u9fff]*线)?([^线杆]+杆)?',
            site,
        )
        if match:
            voltage, kv, line, number, pole = (
                match.group(1),
                match.group(2),
                match.group(3),
                match.group(4),
                match.group(5),
            )
            if voltage:
                if kv != 'kV':
                    explain += f'行{idx}:电压单位不正确。'
                    suggestion += f'行{idx}:修改单位为kV。'
            else:
                explain += f'行{idx}:缺少电压等级。'
                suggestion += f'行{idx}:补充电压等级。'
            if line:
                if number is None:
                    explain += f'行{idx}:线路缺少设备名称。'
                    suggestion += f'行{idx}:补充设备名称。'
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


def re_plan_time(start_time: str, end_time: str) -> Dict:
    """识别计划工作时间"""

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


def re_workperson_sign(person: str, person_sign: str) -> Dict:
    explain = suggestion = ''
    per_set = set(person.split(','))
    sign_set = set(person_sign.split(','))
    if not per_set.issubset(sign_set):
        explain += '工作班签名不完整。'
        suggestion += '检查工作班成员签名。'
    if explain != '':
        return {
            'node': '8.工作班成员签名',
            'satisfied': '0',
            'rule': '5',
            'explain': explain,
            'suggestion': suggestion,
        }
    return {}


def rec_re_ticket1(tk: Dict) -> List[Dict[str, str]]:
    """
    根据正则表达式判断工作票规范性
    func，识别某个栏的函数，args 输入参数名称
    | func          |  arg1              |          arg2          |arg3   |
    |re_work_person | 名字               | 人数                    |
    |re_outage_line |停电线路名称         |
    |re_work_site   |工作地点(列表)       |
    |re_plan_time   |开始时间            | 结束时间                         |
    第一种工作票
    """
    results = []
    results.append(
        re_work_person(
            tk['SGDistributionFirstWorkTicket'][0]['workingPerson'].split('|')[0],
            len(tk['SGDistributionFirstWorkTicket'][0]['workingPerson'].split('|')[1].split(',')),
        )
    )
    results.append(re_outage_line(tk['SGDistributionFirstWorkTicket'][0]['lineName']))
    results.append(re_work_site([x['workPlace'] for x in tk['SGTaskList']]))
    results.append(
        re_plan_time(
            tk['SGDistributionFirstWorkTicket'][0]['scheduledStartTime'],
            tk['SGDistributionFirstWorkTicket'][0]['plannedEndTime'],
        )
    )
    results.append(
        re_workperson_sign(
            tk['SGDistributionFirstWorkTicket'][0]['workingPerson'].split('|')[1],
            tk['SGDistributionFirstWorkTicket'][0]['workingpersonSign'],
        )
    )
    results = list(filter(None, results))
    return results


def rec_re_ticket2(tk: Dict) -> List[Dict[str, str]]:
    """第二种工作票"""
    results = []
    results.append(
        re_work_person(
            tk['SGDistributionSecondWorkticket'][0]['workingPerson'],
            tk['SGDistributionSecondWorkticket'][0]['number'],
        )
    )
    results.append(re_work_site([x['workPlace'] for x in tk['SGTaskList']]))
    results.append(
        re_plan_time(
            tk['SGDistributionSecondWorkticket'][0]['scheduledStartTime'],
            tk['SGDistributionSecondWorkticket'][0]['plannedEndTime'],
        )
    )
    results = list(filter(None, results))
    return results


def rec_re_breakfix(tk: Dict) -> List[Dict[str, str]]:
    """紧急故障抢修单"""
    results = []
    results.append(
        re_work_person(
            tk['SGEmergencyRepairWorkticket'][0]['workingPerson'],
            tk['SGEmergencyRepairWorkticket'][0]['number'],
        )
    )
    results.append(re_work_site([x['workPlace'] for x in tk['SGTaskList']]))
    results = list(filter(None, results))
    return results


def rec_re_electric1(tk: Dict) -> List[Dict[str, str]]:
    results = []
    results.append(
        re_work_person(
            tk['SGEmergencyRepairWorkticket'][0]['workingPerson'],
            len(tk['SGEmergencyRepairWorkticket'][0]['workingPerson'].split(',')),
        )
    )
    results.append(re_work_site([x['workPlace'] for x in tk['SGTaskList']]))
    results = list(filter(None, results))
    return []


def rec_re_electric2(tk: Dict) -> List[Dict[str, str]]:
    results = []
    results.append(
        re_work_person(
            tk['SGEmergencyRepairWorkticket'][0]['workingPerson'],
            len(tk['SGEmergencyRepairWorkticket'][0]['workingPerson'].split(',')),
        )
    )
    results.append(re_work_site([x['workPlace'] for x in tk['SGTaskList']]))
    results = list(filter(None, results))
    return []


def rec_re(ticket_type: str, tk: Dict) -> List:
    results = []
    if ticket_type == 'ticket1':
        results = rec_re_ticket1(tk)
    elif ticket_type == 'ticket2':
        results = rec_re_ticket2(tk)
    elif ticket_type == 'breakfix':
        results = rec_re_breakfix(tk)
    return results


def produce_answer(json_dict: Dict, ticket_type: str, rec_method: str = 're') -> List:
    tk: Dict = json_dict
    if 'result' in tk:
        tk = tk['result']
    ans_json = list()
    try:
        if rec_method == 're':
            ans_json = rec_re(ticket_type, tk)
    except KeyError as e:
        ans_json.append(
            {
                'node': 'Error',
                'satisfied': '0',
                'rule': '0',
                'explain': '识别过程遇到错误，检查工作票类型',
                'suggestion': str(e),
            }
        )
    return ans_json
