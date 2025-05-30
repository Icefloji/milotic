import json


def gen_to_sse(gen, *, event_type='message'):
    yield 'event: start\ndata: {start}\n\n'
    for chunk in gen:
        yield f'event: {event_type}\ndata: {json.dumps(chunk, ensure_ascii=False)}\n\n'
    yield 'event: end\ndata: {end}\n\n'


def str_to_gen(s: str, *, chunk_size=10):
    """将字符串转换为生成器，每次生成指定大小的字符串"""
    for i in range(0, len(s), chunk_size):
        yield {'type': 'msg', 'content': s[i : i + chunk_size]}
