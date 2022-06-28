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

