from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, FastAPI, File, UploadFile

from citra.audio.rec_audio import ROOT_DIR, ASRService

asr_service = ASRService()


@asynccontextmanager
async def asr_lifespan(app: FastAPI):
    # Load the ML model
    asr_service.load_model()
    yield
    # Clean up the ML models and release the resources
    asr_service.unload_model()


router = APIRouter(lifespan=asr_lifespan)


@router.post('/asr/rec_aduio', summary='语音识别', description='上传mp3,wav文件，返回文字和总结')
async def convert_audio(file: UploadFile = File(...)):  # noqa: B008
    file_path = Path(ROOT_DIR, 'data/recording/audio', str(file.filename))
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    if file_path.exists() and file_path.stat().st_size != file_size:
        import uuid

        file_path = Path(file_path.parent, uuid.uuid4().hex + str(file_path.suffix))
    print(file_path)

    with file_path.open('wb') as f:
        content = await file.read()
        f.write(content)

    result = asr_service.convert(str(file_path))
    return result
