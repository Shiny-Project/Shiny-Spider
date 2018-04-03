import sys
import time

import core.database as database
import core.meta as meta
from core import utils
from core.log import Log
from core import config
from Shiny import ShinyError

Logger = Log()

def renew(job_id, spider_name, path):
    Logger.info('刷新 Spider : [ ' + spider_name + ' ] 数据')
    try:
        spider = utils.load_spider(path)
        getattr(spider, spider_name + 'Spider')().main()  # 执行抓取逻辑
        Logger.info('Spider : [ ' + spider_name + ' ] 刷新成功')
        database.report_job_status(job_id, 'success')
    except ShinyError as e:
        if (e.code == 'duplicated_item'):
            Logger.debug('Spider : [ ' + spider_name + ' ] 无新数据')
            database.report_job_status(job_id, 'success')
        else:
            Logger.error('Spider : [ ' + spider_name + ' ] 刷新失败: ' + str(e))
            database.report_job_status(job_id, 'failed')
    except Exception as e:
        Logger.error('Spider : [ ' + spider_name + ' ] 刷新失败: ' + str(e))
        database.report_job_status(job_id, 'failed')

def renew_by_path(path, spider_name):
    Logger.info('刷新 Spider / Path = [ ' + path + ' ] 数据')
    Logger.warning('手动刷新不会刷新任务分发列表 亦不会反馈状态 但新数据仍被广播')
    try:
        spider = utils.load_spider(path)
        getattr(spider, spider_name + 'Spider')().main()  # 执行抓取逻辑
        Logger.info('Spider / Path = [ ' + path + ' ] 刷新成功')
    except ShinyError as e:
        if (e.code == 'duplicated_item'):
            Logger.debug('Spider : [ ' + spider_name + ' ] 无新数据')
        else:
            Logger.error('Spider : [ ' + spider_name + ' ] 刷新失败: ' + str(e))
    except Exception as e:
        Logger.error('Spider : [ ' + spider_name + ' ] 刷新失败: ' + str(e))


def show_version():
    print(meta.project + ' ' + meta.version)


def start_spiders():
    Logger.info('爬虫就绪')
    while True:
        job_list = database.get_job_list()
        if job_list:
            for job in job_list:
                renew(job["id"], job["spider"], job["path"])
        else:
            Logger.warning('当前任务列表为空')
        time.sleep(15)


def main():
    # 初始化
    if len(sys.argv) == 1:
        # 如果是命令行调用 走下面的流程
        print('''
            Usages:

            Main.py <command> [params]

            Command:

            renew <spider_path> <spider_name> : call a specified spider

            ignite : start main progress

            Others:

            --version : show version information
        ''')
    elif len(sys.argv) >= 2:
        # 命令行调用刷新API数据
        command = sys.argv[1]
        if command in ['renew']:
            if len(sys.argv) >= 4:
                spider_path = sys.argv[2]
                spider_name = sys.argv[3]
                renew_by_path(spider_path, spider_name)
            else:
                # 参数缺失
                print('''
                    Parameter Missed

                    Usage:

                    Main.py renew <spider_path> <spider_name>
                ''')
        elif command in ['-version', '--version', 'version']:
            # 显示版本号
            show_version()

        elif command in ['ignite', 'start', 'lift']:
            # 主程序启动
            start_spiders()

            while True:
                time.sleep(1)

    exit()


if __name__ == "__main__":
    main()
