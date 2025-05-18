from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.responses import StreamingResponse

from citra.rag.rag_query import ask_rag, load_retriever

retriever = None


@asynccontextmanager
async def asr_lifespan(app: FastAPI):
    # Load the ML model
    global retriever
    retriever = load_retriever()
    yield
    # Clean up the ML models and release the resources


router = APIRouter(lifespan=asr_lifespan)


@router.get('/rag_question', summary='知识库查询', description='用户提问，根据知识库返回查询结果')
async def ask_question(question: str):
    return StreamingResponse(ask_rag(retriever, question), media_type='text/event-stream')
