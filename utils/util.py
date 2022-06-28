# -*- coding: utf-8 -*-

import re


def process_1(article: str) -> str:
    """特殊处理函数：表格中 企业名称、地点 无分隔符，整篇文章无分隔符变成一句话，ner识别率大大降低。
    http://scjg.xiangyang.gov.cn/zwdt/tzgg/gzgg/202205/t20220519_2808004.shtml
    """
    sub_article = (re.sub('老河口✓{1,3}\d{1,3}|老河口市✓{1,3}\d{1,3}|东津✓{1,3}\d{1,3}|\S{1,2}[市|区|县]✓{1,3}\d{1,3}', '。', article))
    # print(sub_article)

    return sub_article


