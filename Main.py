import config, meta, database
from log import Log
import sys, time, socket, threading

Logger = Log()

def renewData(api_id, Logger = Logger):
    try:
        spiderName = database.getSpiderName(api_id)
        Logger.info('获得映射 : [ ' + api_id + ' -> ' + spiderName + ' ] 尝试刷新')
        Spider = __import__(spiderName + 'Spider')
        Spider = getattr(Spider, spiderName + 'Spider')()
        Spider.main()
    except Exception as e:
        Logger.error('刷新API数据失败[ API ID = ' + api_id + ' ] : ' + str(e))


def showVersionInfo():
    print(meta.project + ' ' + meta.version);


def main():
    # 初始化
    sys.path.append("spiders");
    Logger = Log();
    if (len(sys.argv) == 1):
        # 如果是命令行调用 走下面的流程
        print('''
            Usages:

            Main.py <command> [params]

            Command:

            renew <api_id> : renew the data of the API

            Others:

            --version : show version information
        ''');
    elif (len(sys.argv) >= 2):
        # 命令行调用刷新API数据
        command = sys.argv[1];
        if (command == 'renew'):
            if (len(sys.argv) >= 3):
                api_id = sys.argv[2];
                renewData(api_id, Logger);
            else:
                # 参数缺失
                print('''
                    Parameter Missed

                    Usage:

                    Main.py renew <api_id>
                ''')
        elif (command == '-version' or command == '--version' or command == 'version'):
            showVersionInfo();

        elif (command == 'start'):
            while True:
                Logger.info('正在查询未完成的抓取任务')
                recentJobs = database.getRecentJobs()
                if len(recentJobs) > 0:
                    Logger.info('共有 ' + str(len(recentJobs)) + ' 项任务需要执行')
                    for job in recentJobs:
                        Logger.info('正在进行抓取 [ 任务ID = ' + str(job.id) + ' ] 的抓取任务')
                        renewData(job.api_id)
                        database.deleteJob(job.id)
                else:
                    Logger.info('无任务呢')

                Logger.debug('任务完成..正在冷却..')
                time.sleep(30)


    exit();


if __name__ == "__main__":
    main();
