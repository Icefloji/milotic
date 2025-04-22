# %%
from funasr import AutoModel 
from pathlib import  Path
import json
from openai import OpenAI

# %%
model = AutoModel(model="models/paraformer_zh",vad_model="models/fsmn",  punc_model="models/punc_ct",  spk_model="models/cam++",\
                   disable_update=True,device="cuda:0")
client = OpenAI(
    api_key="sk-64a9aed1c4994164b03fc5f2df35cae7",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

# %%
def make_sumary(paragraph:str)->str|None:
    completion = client.chat.completions.create(
        model="qwen-plus",
        messages=[
        {'role': 'system', 'content': "总结用户的诉求，并给出解决方案。"},
        {'role': 'user', 'content': paragraph}
        ]
    )
    return completion.choices[0].message.content

def convert(input:str):
    res = model.generate(input=input,)
    slice_info=res[0]['sentence_info']
    text=''
    spk_id=0
    talk=[]
    for slice in slice_info:
        if spk_id==slice['spk']:
            text+=slice['text']
        else:
            talk.append({'spk':spk_id,'text':text})
            text=slice['text']
            spk_id=slice['spk']
    talk.append({'spk': spk_id, 'text': text})

    res=make_sumary(res[0]['text'])
    return {'file_name':input.split('/')[-1],'talk':talk,'summary':res,'code':'successed'}

def convert_records(record_file:str,save_type:str='json',output:str='result'):
    """
    record_file: str, 语音文件或文件夹路径
    save_type: str, 保存格式，json或txt，默认json
    保存在文件或文件夹的 同级目录/result下
    """
    #检查文件存在性
    records=[]
    supported_suffixes=['.mp3','.wav']
    rf_path=Path(record_file)
    if rf_path.is_file():
        if rf_path.suffix not in supported_suffixes:
            raise TypeError('not an audio file!')        
        records.append(rf_path)  
    elif rf_path.is_dir(): 
        for file in rf_path.iterdir():
            if file.suffix in supported_suffixes:
                records.append(file)
    if len(records)==0:
        raise FileNotFoundError('folder is empty!')
    #语音转文字
    save_path=rf_path.parent/output
    if not save_path.exists():
        save_path.mkdir()
    for rf in records:
        try: 
            res=convert(str(rf))
        except  Exception as e:
            print(f'文件{rf}转换失败，错误信息：{e}')
            continue
        with (save_path/ (rf.stem+'.json')).open('w', encoding='utf-8') as f:
            json.dump(res, f, ensure_ascii=False, indent=4)
    print("转换完成，保存结果到result文件夹。")
    return 

# %%
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import shutil

app = FastAPI()
upload=Path("uploads")
upload.mkdir(exist_ok=True)
@app.post("/upload")
async def transcribe_audio(file: UploadFile = File(...)):
    save_path = upload/str(file.filename)
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    result =convert(str(save_path))
    return JSONResponse(content=result)


