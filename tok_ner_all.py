# -*- coding: utf-8 -*-

import re
import os
import time
import hanlp

from typing import Generator
from hanlp_common.document import Document
from hanlp.utils.rules import split_sentence

from utils.constants import SPECIAL_DICT
from utils import util

DIR_PATH = '/home/ap/bims/ebo_datas'  # 1.爬虫生成的txt存储的路径，只处理sjxx_前缀开头的文本（sjxx_20220624.txt）；2.ETL需要处理的txt文本也要放在这个路径


def main():
    t1 = time.time()

    # 1.读取/home/ap/bims/ebo_datas路径下所有的商机信息txt文本
    sjxx_list = list()
    files = os.listdir(DIR_PATH)
    for file in files:
        f_tuple = os.path.splitext(file)
        if f_tuple[0].startswith('sjxx_') and (f_tuple[1] == '.txt'):
            sjxx_list.append(file)

    if not sjxx_list:
        print('没有爬虫对应的txt文本')
        return

    # 2.循环处理每天的商机信息txt文本
    for sjxx in sjxx_list:
        nlp_process_dict = {}  # 字典去重
        with open(os.path.join(DIR_PATH, sjxx), 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # 只需一次加载模型即可，不要在处理文章的循环中重复加载模型，会耗时很长！
        HanLP = hanlp.pipeline() \
            .append(hanlp.load('./models/tok/fine_electra_small_20220217_190117'), output_key='tok') \
            .append(hanlp.load('./models/ner/msra_ner_electra_small_20220215_205503'), output_key='ner',
                    input_key='tok')

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

        with open(os.path.join(DIR_PATH, 'nlp_{}.txt'.format(sjxx.split('.')[0].split('_')[1])), 'w',
                  encoding='utf-8') as f:
            for key, value in nlp_process_dict.items():
                f.write('{} {}\n'.format(key, ','.join(value)))

    t2 = time.time()
    print('程序耗时{}秒'.format(round(t2 - t1, 3)))


if __name__ == '__main__':
    main()
