import re

import pandas as pd

ROOT_DIR = 'e:/code/python/WangXiang'


def cut_head(s: str) -> str:
    pat_ignore = r'[^\u4e00-\u9fa5]*([\u4e00-\u9fa5\d]*)[^\u4e00-\u9fa5\d]?'
    match = re.match(pat_ignore, s)
    if match:
        addr = match.group(1)
        search_phone = re.search(r'(/d{11})', s)
        if search_phone:
            addr += search_phone.group(1)
        return addr
    else:
        return ''


filename = '95598-1.xlsx'
df1: pd.Series = pd.read_excel(f'{ROOT_DIR}/data/address/{filename}').iloc[:, 0]
df2: pd.Series = df1.apply(cut_head)

prov_town = r'(?P<省>[^省]{2,5}(省|自治区))?(?P<市>[^市]{2,3}市)?(?P<县>[\u4e00-\u9fa5]{2,4}(县|市|区))?(?P<街道>[\u4e00-\u9fa5]{2,4}(街道|镇))?'  # noqa: E501
cun_street = r'(?P<行政村>[\u4e00-\u9fa5]{2,4}(行政村|村|社区))?(?P<自然村>[\u4e00-\u9fa5]{2,4}(自然村|村|居委会))?(?P<路>[\u4e00-\u9fa5]{1,5}(路|街|大道|道|巷))?'  # noqa: E501
num_none = r'(?P<号>\d{1,4}号)?(?P<区>[\u4e00-\u9fa5A-Za-z\d]{1,5}(家|屋|洲|园|苑|小区|区|塘|公寓))?(?P<无用>[\u4e00-\u9fa5\d]*)?'  # noqa: E501
pattern = prov_town + cun_street + num_none
# 名字短的名字都写这里
keywords = {'柯村': '行政村'}


def extract(addr: str, address_pattern=pattern) -> dict:
    match = re.match(address_pattern, addr)
    res = {}
    if match:
        res = match.groupdict()
    # 识别关键字
    for key, value in keywords.items():
        if key in res['无用']:
            # 结果[区]+=‘区’
            res[value] = (res[value] or '') + key
            res['无用'] = res['无用'].replace(key, '')
    # 识别第二次
    match2 = re.search(address_pattern, res['无用'])
    if match2:
        for key, value in match2.groupdict().items():
            if res[key] is None:
                res[key] = value
                res['无用'] = res['无用'].replace((value or ''), '')
    # 特别，加上号
    match3 = re.match(r'[\u4e00-\u9fa5\d]+?\d+号', res['无用'])
    if match3 and res['区'] is None:
        res['号'] = match3.group()
        res['无用'] = res['无用'].replace(match3.group(), '')
    return res


# 测试 单个字符串
addr = '佛堂镇五洲大道张宅路段'
asf = extract(cut_head(addr))
print(asf)


df3: pd.DataFrame = df2.apply(extract).apply(pd.Series)


df3['raw'] = df1
# 改名字，删除列
df3.columns = ['省', '市', '县', '街道', '行政村', '自然村', '路', '号', '区', '无用', 'raw']
df3 = df3.drop(columns=['无用'])
df3.to_excel(f'{ROOT_DIR}/data/address/parse_{filename}', index=False)
