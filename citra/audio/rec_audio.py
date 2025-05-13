# %%
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

# %%
load_dotenv()
api_key = os.getenv('DASHSCOPE_API_KEY') or ''
ROOT_DIR = os.getenv('ROOT_DIR') or str(Path(__file__).parents[2])
client = OpenAI(api_key=api_key, base_url='https://dashscope.aliyuncs.com/compatible-mode/v1')


# %%
class ASRService:
    def load_model(self, root_dir: str = ''):
        from funasr import AutoModel

        if ROOT_DIR:
            root_dir = ROOT_DIR
        try:
            self.model = AutoModel(
                model=f'{root_dir}/models/paraformer_zh',
                vad_model=f'{root_dir}/models/fsmn',
                punc_model=f'{root_dir}/models/punc_ct',
                spk_model=f'{root_dir}/models/cam++',
                disable_update=True,
            )
        except FileNotFoundError as e:
            raise FileNotFoundError('模型文件不存在，请检查路径是否正确！') from e

    def unload_model(self):
        self.model = None

    def make_sumary(self, paragraph: str) -> str:
        completion = client.chat.completions.create(
            model='qwen-plus',
            messages=[
                {
                    'role': 'system',
                    'content': """你是电力公司的客服，用20个字归纳和用户的咨询通过。模仿以下案例：\
                        客户咨询关于新能源车充电桩安装及电表申请的相关事宜。\
                        客户反映家中停电，供电局未解决问题，怀疑是表后问题，寻求帮助。\
                        客户咨询关于建造房屋时申请临时电表的所需资料。""",
                },
                {'role': 'user', 'content': paragraph},
            ],
        )
        return completion.choices[0].message.content or '请求失败'

    def mp3_to_wav(self, input: str) -> str:
        from pydub import AudioSegment

        audio = AudioSegment.from_mp3(input)
        new_input = input.replace('.mp3', '.wav')
        audio.export(new_input, format='wav')
        return new_input

    def convert(self, input: str) -> dict:
        if input.endswith('.mp3'):
            input = self.mp3_to_wav(input)
        if self.model:
            res = self.model.generate(input=input)
            slice_info = res[0]['sentence_info']
            text = ''
            spk_id = 0
            talk = []
            for slice in slice_info:
                if spk_id == slice['spk']:
                    text += slice['text']
                else:
                    talk.append({'spk': spk_id, 'text': text})
                    text = slice['text']
                    spk_id = slice['spk']
            talk.append({'spk': spk_id, 'text': text})
            res = self.make_sumary(res[0]['text'])
            return {'file_name': Path(input).name, 'talk': talk, 'summary': res, 'code': 'successed'}
        else:
            raise RuntimeError('模型未加载')

    def convert_records(self, record_scr: str, save_type: str = 'json', record_dst: str = 'result') -> None:
        # 检查文件存在
        records = []
        supported_suffixes = ['.mp3', '.wav']
        rf_path = Path(record_scr)
        if rf_path.is_file():
            if rf_path.suffix not in supported_suffixes:
                raise TypeError('not an audio file!')
            records.append(rf_path)
        elif rf_path.is_dir():
            for file in rf_path.iterdir():
                if file.suffix in supported_suffixes:
                    records.append(file)
        if len(records) == 0:
            raise FileNotFoundError('folder is empty!')
        # 语音转文字
        save_path = rf_path.parent / record_dst
        if not save_path.exists():
            save_path.mkdir()
        for rf in records:
            try:
                res = self.convert(str(rf))
            except Exception as e:
                print(f'文件{rf}转换失败，错误信息：{e}')
                continue
            with (save_path / (rf.stem + '.json')).open('w', encoding='utf-8') as f:
                json.dump(res, f, ensure_ascii=False, indent=4)
        print('转换完成，保存结果到result文件夹。')
        return


# %%
if __name__ == '__main__':
    asrs = ASRService()
    record = Path('data/recording/audio/1.mp3')
    res = asrs.convert(str(record))
    print(res)
