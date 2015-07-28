import config,meta,database
from log import Log 
import sys,time,socket,threading

def tcpLinkHandler(socket, address, Logger):
    Logger.info('接受来自 %s:%s 的连接' % address)
    while True:
        data = socket.recv(1024)
        if data:
            try:
                api_id = data.decode('utf-8')
                Logger.info('刷新API:' + api_id)
                renewData(api_id, Logger)
            except Exception as e:
                Logger.error('刷新API数据失败' + str(e))
        else:
            break
    socket.close()

def renewData(api_id, Logger):
    try:
        spiderName = database.getSpiderName(api_id)
        Logger.info('获得映射 : [' + api_id + '->' + spiderName + '] 尝试刷新')
        Spider = __import__(spiderName + 'Spider')
        Spider = getattr(Spider, spiderName + 'Spider')()
        Spider.main()
    except Exception as e:
        Logger.error('刷新API数据失败[' + api_id + '] : ' + str(e))

def showVersionInfo():
    print(meta.project + ' ' + meta.version);

def main():
    #初始化
    sys.path.append("spiders");
    Logger = Log();
    if (len(sys.argv) == 1):
        #如果是命令行调用 走下面的流程
        print('''
            Usages:

            Main.py <command> [params]

            Command:

            renew <api_id> : renew the data of the API

            Others:

            --version : show version information
        ''');
    elif (len(sys.argv) >= 2):
        #命令行调用刷新API数据
        command = sys.argv[1];
        if (command == 'renew'):
            if (len(sys.argv) >= 3):
                api_id = sys.argv[2];
                renewData(api_id,Logger);
            else:
                #参数缺失
                print('''
                    Parameter Missed

                    Usage:

                    Main.py renew <api_id>
                ''')
        elif (command == '-version' or command == '--version' or command == 'version'):
            showVersionInfo();

        elif (command == 'start'):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM);
            sock.bind(('localhost', 3939))  #socket监听3939端口
            sock.listen(5) #设置最大允许连接数，各连接和server的通信遵循FIFO原则  
            Logger.info('服务器已启动 监听端口 : ' + str(3939) + ' 正在等待连接'),
            while True:
                connection,address = sock.accept()
                try:
                    #创建线程处理新连接
                    thread = threading.Thread(target=tcpLinkHandler, args=(connection, address, Logger))
                    thread.start();
                    #connection.settimeout(120);
                except socket.timeout:
                    Logger.error('socket连接超时')

    exit();


if __name__ == "__main__":
    main();


