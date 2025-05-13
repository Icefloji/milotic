import json
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field, field_validator

from citra.ticket.recognize import produce_answer


class TicketDict(BaseModel):
    ticket_type: str = Field('ticket1', description='票类型', title='tic')
    rec_method: str = 're'
    ticket_dict: dict

    @field_validator('ticket_type')
    def tik_category(cls, tc):
        if tc not in {'ticket1', 'ticket2', 'breakfix'}:
            raise ValueError('invalid ticket type')
        return tc

    @field_validator('rec_method')
    def tik_method(cls, tm):
        if tm not in {'re', 'ai'}:
            raise ValueError('invalid ticket type')
        return tm

    @field_validator('ticket_dict')
    def check_dict(cls, td):
        if 'result' not in td:
            raise ValueError('dict without item result')
        return td


class TicketRes(BaseModel):
    status: Literal['success', 'fail'] = 'fail'
    message: str = ''
    ticket_type: str = ''
    errors: list = []
    error_count: int = 0


router = APIRouter()


@router.post('/upload_ticket', summary='核对工作票', description='上传工作票，返回核对结果')
async def inspect_ticket(tic: TicketDict) -> dict:
    response = TicketRes(status='fail')
    try:
        response.errors = produce_answer(tic.ticket_dict, tic.ticket_type, tic.rec_method)
        response.status = 'success'
        response.message = 'inspect successfully'
        response.ticket_type = tic.ticket_type
        response.error_count = len(response.errors)
    except Exception as e:
        response.message = f'error occurs when recognizing ticket:{e}'
    return json.loads(response.model_dump_json())
