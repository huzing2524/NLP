### NLP（自然语言处理）功能：

- 【功能说明】：
    - 基于开源项目 [HanLP](https://github.com/hankcs/HanLP) 开发而来，主要工作是修改模型的配置项，使其在离线环境加载模型，实现 `分词` 和 `命名实体识别` 功能。
    - 项目需求：在外网每天抓取政府机关、门户网站、新闻网站、财经新闻等各类新闻，存储入库后在离线环境做NLP提取公司名称，匹配关键词并打标签，给对公商机系统提供部分数据。寻找出优质公司，为贷款提供依据。
    - 流程：外网 --> 爬虫 --> 内网 转换为txt存储 (business_news/sjxx_20220617.txt) --> NLP --> ETL
    - 数据来源说明：商机新闻存储在business_news目录下，每天爬虫会抓取新闻存储在一个文件中，文件名以sjxx_为前缀、以日期结尾，一个txt文件中一条数据库记录存储为一行，以换行符分隔。字段顺序为：dataFrom, dataType, title, describe, sitename, putDate, keword, dataCode, dataDetail, url, localpath。其中dataDetail为新闻内容，url为新闻的链接，字段以###分隔。

- 【程序运行命令】：
    nohup命令需要指定接收输出流的位置，否则会终端中会阻塞状态运行。
    - 使用APScheduler开启定时任务，处理当天的数据（每天 ?时 ?分 执行一次）：
        `nohup python tok_ner_scheduler.py --hour 12 --minute 00 >> ./nohup.out 2>&1 &`
    - 立即处理所有的商机新闻txt文件：
        `python tok_ner_all.py`

- 【环境】：
    - OS：ubuntu 20.04
    - Python：3.7.7
    - 依赖包：`pip install -r requirements.txt`

