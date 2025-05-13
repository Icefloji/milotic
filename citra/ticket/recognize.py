# %%
import json
import os
import re
from pathlib import Path

from ollama import ChatResponse, chat
from openai import OpenAI

ROOT_DIR = 'E:/code/python/WangXiang' or os.getenv('ROOT_DIR')


# %%
client = OpenAI(
    api_key=os.getenv('DASHSCOPE_API_KEY'),
    base_url='https://dashscope.aliyuncs.com/compatible-mode/v1',
)


# %%
def get_question(rule: str, instance: str):
    return f"""## 任务
    请检查以下文档是否符合以下合规要求。每条规则只检测 规则中的【】项。如果项内容为空，则跳过检测。
    输出*json格式*结果，包括错的误项node，匹配的规则rule，是否合规satisfi（0或1），的解析explain，修改建议suggestion。
    [{{
        'node':'1',
        'satisfied':'0',
        'rule':'2',
        'explain':'天数为20天，超出规则设定的15天',
        'suggestion':'检查天数是否填写错误'
    }}]
    ##规则
    {rule}

    ##文档
    {instance}
    """


# %%
def ask(question: str) -> str:
    completion = client.chat.completions.create(
        model='qwen-max',
        messages=[
            {
                'role': 'system',
                'content': '你是一个文档校对助手，请根据*规则*，判断*文档*的填写规范性。',
            },
            {'role': 'user', 'content': question},
        ],
    )
    return completion.choices[0].message.content or ''


def ask_local(question: str) -> str:
    response: ChatResponse = chat(
        model='qwen2.5:3b',
        messages=[
            {
                'role': 'system',
                'content': '你是一个文档校对助手，请根据*规则*，判断*文档*的填写规范性。',
            },
            {'role': 'user', 'content': question},
        ],
    )
    return response.message.content or ''


# %%
def convert_json(answer: str) -> list:
    pattern = r'(\[[^\]]+\])'
    search = re.search(pattern, answer)
    if search:
        return json.loads(search.group())
    else:
        return list()


# %%
def get_rule(ticket_type: str) -> str:
    rule_path = Path(ROOT_DIR, 'data/ticket/', ticket_type, 'rule.txt')
    with rule_path.open('r', encoding='utf-8') as rf:
        rule = rf.read()
    return rule


# %%
def rec_re(ticket_type: str, tk: dict) -> list:
    results = []
    if ticket_type == 'ticket1':
        from citra.ticket.regex import rec_re_ticket1

        results = rec_re_ticket1(tk)
    elif ticket_type == 'ticket2':
        from .regex import rec_re_ticket2

        results = rec_re_ticket2(tk)
    elif ticket_type == 'breakfix':
        from .regex import rec_re_breakfix

        results = rec_re_breakfix(tk)

    return results


# %%
def produce_answer(json_dict: dict, ticket_type: str, rec_method: str = 're') -> list:
    tk: dict = json_dict
    if 'result' in tk:
        tk = tk['result']
    ans_json = list()
    try:
        if rec_method == 'ai':
            from .generate import get_ticket

            instance = get_ticket(ticket_type, tk)
            rule = get_rule(ticket_type)
            question = get_question(rule, instance)
            answer = ask(question)
            ans_json = convert_json(answer)
        elif rec_method == 're':
            ans_json = rec_re(ticket_type, tk)
    except Exception as e:
        raise Exception(f'error occurs when recognizing ticket:{e}')  # noqa: B904
    return ans_json


# %%
if __name__ == '__main__':
    json_str = open(r'E:/code/python/WangXiang/data/ticket/ticket.json', encoding='utf-8').read()
    tk = json.loads(json_str)['result']
    res = produce_answer(tk, 'ticket1', rec_method='re')
    print(res)
