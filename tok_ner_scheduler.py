# -*- coding: utf-8 -*-

import re
import os
import time
import datetime
import argparse
import hanlp

from typing import Generator
from hanlp_common.document import Document
from hanlp.utils.rules import split_sentence
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.blocking import BlockingScheduler

from utils.constants import SPECIAL_DICT
from utils import util

"""
一、NLP功能说明：
    文档地址：https://github.com/hankcs/HanLP
    
    ——————————————————————————————————————————————————————————————
    功能             模型       标注标准
    ——————————————————————————————————————————————————————————————
    分词	            tok        粗分、细分
    词性标注	        pos        CTB、PKU、863
    命名实体识别		ner        PKU、MSRA(微软亚洲研究院)、OntoNotes
    依存句法分析		dep        SD、UD、PMT
    成分句法分析		con        Chinese Tree Bank
    语义依存分析		sdp        CSDP
    语义角色标注		srl        Chinese Proposition Bank
    抽象意义表示		amr        CAMR
    指代消解	        暂无        OntoNotes
    语义文本相似度	sts        暂无
    文本风格转换		暂无        暂无
    关键词短语提取	暂无        暂无
    抽取式自动摘要	暂无        暂无
    ——————————————————————————————————————————————————————————————
    
    HanLP发布的模型分为 多任务 和 单任务 两种，多任务速度快省显存，单任务精度高更灵活。
    多任务：
        一个模型实现多种功能
        HanLP = hanlp.load(hanlp.pretrained.mtl.CLOSE_TOK_POS_NER_SRL_DEP_SDP_CON_ELECTRA_BASE_ZH)
        分词、词性标注、命名实体识别、语义角色标注、依存句法分析、语义依存分析、成分句法分析
    单任务：
        一个模型只有单种功能，流水线模式组装调用，需要注意先后顺序。命名实体识别任务的输入为已分词的句子！！！
        NER命名实体识别 单任务 预训练模型：
        文档地址：https://hanlp.hankcs.com/docs/api/hanlp/pretrained/ner.html
        1. hanlp.pretrained.ner.CONLL03_NER_BERT_BASE_CASED_EN
           BERT model (Devlin et al. 2019) trained on CoNLL03.
        2. hanlp.pretrained.ner.MSRA_NER_ALBERT_BASE_ZH
           ALBERT model (Lan et al. 2020) trained on MSRA with 3 entity types.
        3. hanlp.pretrained.ner.MSRA_NER_BERT_BASE_ZH
           BERT model (Devlin et al. 2019) trained on MSRA with 3 entity types.
        4. hanlp.pretrained.ner.MSRA_NER_ELECTRA_SMALL_ZH
           Electra small model (Clark et al. 2020) trained on MSRA with 26 entity types. F1 = 95.16
    
    NER命名实体识别 代码逻辑：
        1.分句           基于规则的分句函数。                       (Native API的输入单位限定为句子sentences，需使用 多语种分句模型 或 基于规则的分句函数 先行分句。)
        2.分词           模型：tok, 标注标准：粗分/细分。            (Tokenization is a way of separating a sentence into smaller units called tokens. In lexical analysis, tokens usually refer to words.)
        3.命名实体识别    模型：ner, 标注标准：PKU、MSRA、OntoNotes。 (Named-entity recognition: 文本中有一些描述实体的词汇。比如人名、地名、组织机构名、股票基金、医学术语等，称为 命名实体。具有以下共性: 数量无穷、构词灵活、类别模糊。)
    
    API方法：
        1.分句(sentences)：
            re.sub(r'([。！？?])([^”’])', r"\1\n\2", text)，除了逗号的标点符号会被替换为换行符，然后文本会被切分成sentences。
            一个句子越长，识别准确率越低，耗时越长。没有标点符号或者全为逗号，文本会变成一个句子。
            # 方法一
            gen = split_sentence('文本内容')  # type: Generator[str]
            # 方法二
            # HanLP = hanlp.pipeline().append(hanlp.utils.rules.split_sentence, output_key='sentences')
        2.分词(tok) + 命名实体识别(ner)：
            # 方法一：离线模式，使用本地路径下的模型
            HanLP = hanlp.pipeline() \
                .append(hanlp.utils.rules.split_sentence, output_key='sentences') \
                .append(hanlp.load('tok/fine_electra_small_20220217_190117'), output_key='tok') \
                .append(hanlp.load('ner/msra_ner_electra_small_20220215_205503'), output_key='ner', input_key='tok')
            # 方法二：使用网络下载模型，模型下载到本机的文件夹路径为 C:\\Users\\huzing2524\\AppData\\Roaming\\hanlp\\tok\\fine_electra_small_20220217_190117.zip
            HanLP = hanlp.pipeline() \
                .append(hanlp.utils.rules.split_sentence, output_key='sentences') \
                .append(hanlp.load('FINE_ELECTRA_SMALL_ZH'), output_key='tok') \
                .append(hanlp.load('MSRA_NER_ELECTRA_SMALL_ZH'), output_key='ner', input_key='tok')
    
    修改模型配置项：
        【此项改动可以使下面的文件从本地项目的目录中加载，不再从网络下载到Windows或者Linux的根目录并从此路径加载】
        tok：
            ./models/tok/fine_electra_small_20220217_190117/config.json 中的 "transform": {"mapper": "https://file.hankcs.com/hanlp/utils/char_table_20210602_202632.json.zip"}
            更改为："transform": {"mapper": "./config/char_table_20210602_202632.json"}
        ner:
            ./models/ner/msra_ner_electra_small_20220215_205503/config.json 中的 "transform": {"mapper": "https://file.hankcs.com/hanlp/utils/char_table_20210602_202632.json.zip"}
            更改为："transform": {"mapper": "./config/char_table_20210602_202632.json"}
        transformers:
            ./models/tok/fine_electra_small_20220217_190117/config.json 和 ./models/ner/msra_ner_electra_small_20220215_205503/config.json 中的 "transformer": "hfl/chinese-electra-180g-small-discriminator"
            更改为："transformer": "./models/transformers/electra_zh_small_20210706_125427"

二、爬虫、ETL功能流程说明：
    外网 --> 爬虫 --> SQLite存储 --> 内网65服务器 --> 转换为txt存储 /home/ap/bims/ebo_datas/sjxx_20220624.txt --> NLP --> ETL
    外网服务器上的爬虫抓取到的新闻是存储在SQLite数据库中（SQLite不支持远程访问）
    内网服务器上商机新闻以txt文本方式存储：
        1. 每天的新闻存储在一个txt文件中（文件命名：sjxx_年月日.txt）
        2. 不同新闻以换行分隔符区分，每一行文本是一条商机新闻
        3. 一条新闻中，以分隔符 ### 区分SQLite中不同的字段信息
        4. 字段顺序（dataFrom, dataType, title, describe, sitename, putDate, keword, dataCode, dataDetail, url, localpath）
"""

DIR_PATH = '/home/ap/bims/ebo_datas'  # 1.爬虫生成的txt存储的路径，只处理sjxx_前缀开头的文本（sjxx_20220624.txt）；2.ETL需要处理的txt文本也要放在这个路径


def main():
    t1 = time.time()
    today = datetime.datetime.now().strftime('%Y%m%d')

    # 1.读取当日商机信息txt文本
    nlp_process_dict = {}  # 字典去重
    if not os.path.exists(os.path.join(DIR_PATH, 'sjxx_{}.txt'.format(today))):
        print('没有爬虫对应的txt文本')
        return
    with open(os.path.join(DIR_PATH, 'sjxx_{}.txt'.format(today)), 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 只需一次加载模型即可，不要在处理文章的循环中重复加载模型，会耗时很长！
    HanLP = hanlp.pipeline() \
        .append(hanlp.load('./models/tok/fine_electra_small_20220217_190117'), output_key='tok') \
        .append(hanlp.load('./models/ner/msra_ner_electra_small_20220215_205503'), output_key='ner', input_key='tok')

    for line in lines:
        line_list = line.split('###')
        url, news = line_list[-2], line_list[-3]
        # 特殊处理过程
        if url in SPECIAL_DICT:
            func = getattr(util, SPECIAL_DICT[url])
            article = func(news)
        else:
            article = news
        # print(article, '\n')

        # 2.判断整篇文章是否有关键词标签
        label_list = re.findall('专精特新|单项冠军企业|新型基础设施|小巨人|制造业项目|绿色环保|隐形冠军', article)  # type: list
        if not label_list:
            continue
        label_list = list(set(label_list))

        # 3.分句(sentences)
        gen = split_sentence(article)  # type: Generator[str]

        for g in gen:
            # 4. 判断句子中是否有关键词"公司"
            if not re.findall('公司', g):  # type: list
                continue

            # 5.分词(tok) + 命名实体识别(ner)
            document = HanLP(g)  # type: Document
            ner = document['ner']  # type: list
            # print('ner', ner)

            for n in ner:
                # [命名实体, 类型标签, 起始下标, 终止下标]，下标指的是命名实体在单词数组中的下标。
                if (len(n[0]) > 2) and ('公司' in n[0]) and (n[1] == 'ORGANIZATION'):
                    if n[0] in nlp_process_dict:  # 合并相同公司名称的标签
                        nlp_process_dict[n[0]] = list(set(label_list + nlp_process_dict[n[0]]))  # type: list
                    else:  # 新增一个公司
                        nlp_process_dict[n[0]] = label_list  # type: list

    with open(os.path.join(DIR_PATH, 'nlp_{}.txt'.format(today)), 'w', encoding='utf-8') as f:
        for key, value in nlp_process_dict.items():
            f.write('{} {}\n'.format(key, ','.join(value)))

    t2 = time.time()
    print('程序耗时{}秒'.format(round(t2 - t1, 3)))


if __name__ == '__main__':
    # 使用APScheduler开启定时任务
    parser = argparse.ArgumentParser(description='对公商机系统，NLP命名实体识别提取公司名称和关键词')
    parser.add_argument('--hour', type=int, help='开启定时任务，将处理当天的数据。指定该参数，该程序将于 每天 12时 运行')
    parser.add_argument('--minute', type=int, help='开启定时任务，将处理当天的数据。指定该参数，该程序将于 每天 00分 运行')
    args = parser.parse_args()

    assert args.hour, '需要定时任务中的hour参数'
    assert args.minute, '需要定时任务中的minute参数'

    # https://apscheduler.readthedocs.io/en/latest/modules/triggers/cron.html#module-apscheduler.triggers.cron
    # 定时任务：每天 ?时(0-23) ?分(0-59) 执行一次
    # 方法一
    # scheduler.add_job(main, 'cron', args=[args.date], day_of_week='*', hour=args.hour, minute=args.minute)

    # 方法二
    jobstores = {'default': MemoryJobStore()}
    executors = {'default': ThreadPoolExecutor()}
    trigger = CronTrigger(day='*', hour=args.hour, minute=args.minute, timezone='Asia/Shanghai')
    scheduler = BlockingScheduler(jobstores=jobstores, executors=executors)
    scheduler.add_job(main, trigger=trigger, id='0', name='NLP处理函数定时任务', replace_existing=True)

    scheduler.start()
