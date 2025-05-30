from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from citra.rag.query_rag import query_knowledge_base
from citra.service.protocol import gen_to_sse

router = APIRouter()


@router.post('/rag_question', summary='知识库查询', description='用户提问，根据知识库返回查询结果')
async def ask_question(request: Request, body: dict[str, str] = {'question': ''}):
    service_ip = str(request.base_url)
    answer = query_knowledge_base(service_ip, body['question'])
    res_sse = gen_to_sse(answer)
    return StreamingResponse(res_sse, media_type='text/event-stream')
