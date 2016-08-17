import sys
import importlib.util

import database
import meta
from log import Log

Logger = Log()


def renew(spider_name):
    try:
        spider_path = database.get_spider_path(spider_name)
        Logger.info('成功获得 Spider : [ ' + spider_name + ' ]的路径 : [ ' + spider_path + ' ]')

        # 面向StackOverflow编程抄来的代码 根据路径导入包
        spec = importlib.util.spec_from_file_location("example", './spiders/' + spider_path + '.py')
        spider = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(spider)

        getattr(spider, spider_name + 'Spider')().main()  # 执行抓取逻辑

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

            renew <api_id> : renew the data of the API

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

        elif command == ['ignite', 'start', 'lift']:
            # 主程序启动
            pass

    exit()


if __name__ == "__main__":
    main()
