import socket
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

from citra.service.protocol import gen_to_sse
from citra.service.rag import router as rag_router
from citra.service.ticket import router as tik_router

# ruff:noqa: F401 B006
app = FastAPI(docs_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],  # 允许所有域名访问，可以改为具体的域名列表
    allow_credentials=True,
    allow_methods=['*'],  # 允许所有方法，如 GET、POST 等
    allow_headers=['*'],  # 允许所有请求头
)


## 打包时需要将静态文件打包到可执行文件中
def resource_path(relative_path):
    import sys

    """返回运行时的文件路径，兼容 PyInstaller 打包后的路径"""
    if hasattr(sys, '_MEIPASS'):
        return str(Path(sys._MEIPASS, relative_path))  # type: ignore
    return Path(relative_path).resolve()


app.mount('/static', StaticFiles(directory=resource_path('citra/service/static')), name='static')
app.mount('/cache', StaticFiles(directory=resource_path('citra/service/cache')), name='cache')
app.mount('/knowledge_base', StaticFiles(directory=resource_path('data/rag')), name='knowbase')


@app.get('/docs', include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=str(app.openapi_url),
        title=app.title + '-swagger-ui',
        swagger_js_url='/static/swagger-ui/swagger-ui-bundle.js',
        swagger_css_url='/static/swagger-ui/swagger-ui.css',
    )


@app.get('/')
async def hello():
    return 'hello world!'


@app.get('/client')
async def get_client_ip(request: Request):
    client_host = request.base_url
    return {'client_ip': client_host}


# app.include_router(tik_router, tags=['inspection'])
app.include_router(rag_router, tags=['knowledge_base'])


##这里开始看
@app.post('/ai_question', summary='AI问数', description='输入用户的问题，返回数据库结果')
async def ask_outage(body: dict = {'question': ''}):
    from citra.mcp.query_db import consult_database

    try:
        print(body['question'])
        res_gen = consult_database(body['question'])
        res_sse = gen_to_sse(res_gen)
        return StreamingResponse(res_sse, media_type='text/event-stream')
    except Exception as e:
        from citra.service.protocol import str_to_gen

        error = str_to_gen(f'Error: {e}', chunk_size=1000)
        return StreamingResponse(gen_to_sse(error, event_type='err'), media_type='text/event-stream')


@app.post('/chat', summary='闲聊')
async def chat_with_me(body: dict = {'question': '', 'id': 'abc2'}):
    from citra.chat_with_me import talk

    answer = gen_to_sse(talk(body['question'], body['id']))
    return StreamingResponse(answer, media_type='text/event-stream')


def find_available_port(start_port: int):
    """查找可用端口"""
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', start_port))
            return start_port
        except OSError:
            start_port += 1


if __name__ == '__main__':
    available_port = find_available_port(8000)
    uvicorn.run(app, host='0.0.0.0', port=available_port)
