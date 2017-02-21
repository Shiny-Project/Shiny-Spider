import json, sys, time

import core.database as database
import core.meta as meta
from core import utils
from core.log import Log
from core import config


Logger = Log()


def renew(spider_name):
    try:
        spider_path, spider_trigger_time, spider_info = database.get_spider_info(spider_name)
        Logger.debug('成功获得 Spider : [ ' + spider_name + ' ]的路径 : [ ' + spider_path + ' ]')
        timestamp = utils.parse_time_string(spider_trigger_time)
        spider = utils.load_spider(spider_path)
        try:
            if getattr(spider, spider_name + 'Spider')().check(timestamp):
                Logger.debug('[ Spider = ' + spider_name + ' ] 数据未过期')  # 数据没有过期 不执行
            else:
                getattr(spider, spider_name + 'Spider')().main()  # 数据过期 执行抓取逻辑
                database.renew_trigger_time(spider_name)
        except Exception as e:
            print(e)
            if not spider_info:
                Logger.error('[ Spider = ' + spider_name + ' ] 缺少有效期设置')
            else:
                info = json.loads(spider_info)
                if not info['expires']:
                    Logger.error('[ Spider = ' + spider_name + ' ] 缺少有效期设置')
                else:
                    if utils.get_time() - timestamp >= int(info['expires']):
                        getattr(spider, spider_name + 'Spider')().main()  # 数据过期 执行抓取逻辑
                        database.renew_trigger_time(spider_name)
                    else:
                        Logger.debug('[ Spider = ' + spider_name + ' ] 数据未过期')

    except Exception as e:
        Logger.error('抓取数据失败 [ Spider Name = ' + spider_name + ' ] : ' + str(e))


def show_version():
    print(meta.project + ' ' + meta.version)


def main():
    # 初始化
    if len(sys.argv) == 1:
        # 如果是命令行调用 走下面的流程
        print('''
            Usages:

            Main.py <command> [params]

            Command:

            renew <spider_name> : call a specified spider

            ignite : start main progress

            Others:

            --version : show version information
        ''')
    elif len(sys.argv) >= 2:
        # 命令行调用刷新API数据
        command = sys.argv[1]
        if command in ['renew']:
            if len(sys.argv) >= 3:
                spider_name = sys.argv[2]
                renew(spider_name)
            else:
                # 参数缺失
                print('''
                    Parameter Missed

                    Usage:

                    Main.py renew <api_id>
                ''')
        elif command in ['-version', '--version', 'version']:
            # 显示版本号
            show_version()

        elif command in ['ignite', 'start', 'lift']:
            # 主程序启动
            Logger.debug('监视流程启动')
            while True:
                spider_list = database.get_spider_list()
                if spider_list:
                    for spider in spider_list:
                        renew(spider.name)
                else:
                    Logger.warning('没有已经定义的Spider')
                time.sleep(30)

    exit()


if __name__ == "__main__":
    main()
