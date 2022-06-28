部署过程 & 程序运行：

【程序运行命令】
    nohup命令需要指定接收输出流的位置，否则会终端中会阻塞状态运行。
    1. 使用APScheduler开启定时任务，处理当天的数据（每天 ?时 ?分 执行一次）：
        nohup python tok_ner_scheduler.py --hour 12 --minute 00 >> ./nohup.out 2>&1 &
    2. 立即处理所有的商机新闻txt文件：
        python tok_ner_all.py

【安装Python 3.7.7】
    【非必要步骤】如果不能正常编译安装Python和运行tok_ner.py文件，则尝试安装下面的rmp包（x86_64为64位系统的软件包）:
    1. cd /NLP/Deployment_Normal/rpm
    2. rpm -ivh --force --nodeps *

    安装Python：
    1. mkdir -p /usr/local/python3.7
    2. cd NLP/Deployment_Normal/python
    3. tar -zxvf Python-3.7.7.tgz
    4. cd Python-3.7.7/
    5. ./configure --prefix=/usr/local/python3.7 --enable-optimizations --enable-loadable-sqlite-extensions
    6. make && sudo make install
    7. find / -name 'pip3'
    8. mv /usr/bin/python /usr/bin/python_bak
    9. mv /usr/bin/pip /usr/bin/pip_bak
    10. ln -s /usr/local/python3.7/bin/python3.7  /usr/bin/python
    11. ln  -s /usr/local/python3.7/bin/pip3 /usr/bin/pip
    12. vi /usr/libexec/urlgrabber-ext-down
        #! /usr/bin/python 改为 #! /usr/bin/python2.7
    13. vi /usr/bin/yum
        #!/usr/bin/python 改为 #!/usr/bin/python2.7

    检查Python是否安装完成：
    1. whereis python
    2. python -V
    3. pip -V

【安装第三方包】
    1. cd /NLP
    2. pip install --no-index --find-links=Deployment_Normal/site-packages/ -r Deployment_Normal/requirements.txt

【安装Oracle客户端Instant Client】
    官方文档地址：
    https://www.oracle.com/cn/database/technologies/instant-client/linux-x86-64-downloads.html
    https://www.oracle.com/cn/database/technology/linuxx86-64soft.html
    1. sudo cp -r NLP/Deployment_Normal/oracle/ /opt/
    2. cd /opt/oracle
    3. unzip instantclient-basic-linux.x64-19.15.0.0.0dbru-2.zip
    4. unzip instantclient-sqlplus-linux.x64-19.15.0.0.0dbru-2.zip
    5. 安装 libaio 软件包
       5.1 查看是否已经安装：yum list installed | grep libaio
       5.2 如果未安装，执行命令：rpm -ivh libaio-0.3.109-13.el7.x86_64.rpm
    6. vim ~/.bash_profile，编辑输入以下内容：
       6.1 export LD_LIBRARY_PATH=/opt/oracle/instantclient_19_15:$LD_LIBRARY_PATH
       6.2 export PATH=/opt/oracle/instantclient_19_15:$PATH
       6.3 source ~/.bash_profile
    7. 测试连接Oracle数据库：
       7.1 ping 128.1.108.205
       7.2 telnet 128.1.108.205 11521
       7.3 python NLP/oracle.py，输出Oracle数据库版本信息 19.6.0.0.0，说明连接数据库成功
       7.4 sqlplus bims/Bims_2021@128.1.108.205:11521/bims0     （sqlplus 数据库用户名/数据库密码@ip地址:端口号/数据库名称）

【测试环境安装报错】
    报错信息：
    ModuleNotFoundError: No module named '_ctypes'
    Error: Command errored out with exit status 1: python setup.py egg_info Check the logs for full command output.
    解决办法：
    1.安装 libffi-devel-3.0.13-18.el7.x86_64.rpm，
      命令：yum install -y libffi-devel-3.0.13-18.el7.x86_64.rpm
           rpm -ivh libffi-devel-3.0.13-18.el7.x86_64.rpm
    2.重新编译安装Python
      命令：
        1. cd /home/ap/tomcat/python_files/Python-3.7.7 (生产环境Python的安装路径不同，需要更正)
        2. ./configure --prefix=/usr/local/python3.7 --enable-optimizations --enable-loadable-sqlite-extensions
        3. make
        4. sudo make install

    报错信息：
    ModuleNotFoundError: No module named '_sqlite3'
    解决办法：
    1. yum install -y sqlite-devel-3.7.17-8.el7_7.1.x86_64.rpm
    2. cd Python-3.7.7/
    3. ./configure --prefix=/usr/local/python3.7 --enable-optimizations --enable-loadable-sqlite-extensions
    4. make && make install
