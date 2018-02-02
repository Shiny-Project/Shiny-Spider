import json
import sys
import time
import threading

import core.database as database
import core.meta as meta
from core import utils
from core.log import Log
from core import config
from Shiny import ShinyError

Logger = Log()
Database = database.Database()


def renew_by_path(job_id, spider_name, path):
    Logger.info('刷新 Spider : [ ' + spider_name + ' ] 数据')
    try:
        spider = utils.load_spider(path)
        getattr(spider, spider_name + 'Spider')().main()  # 执行抓取逻辑
        Logger.info('Spider : [ ' + spider_name + ' ] 刷新成功')
        Database.report_job_status(job_id, 'success')
    except ShinyError as e:
        if (e.code == 'duplicated_item'):
            Logger.debug('Spider : [ ' + spider_name + ' ] 无新数据')
            Database.report_job_status(job_id, 'success')
        else:
            Logger.error('Spider : [ ' + spider_name + ' ] 刷新失败')
            Database.report_job_status(job_id, 'failed')


def show_version():
    print(meta.project + ' ' + meta.version)


def start_spiders():
    Logger.info('爬虫就绪')
    while True:
        job_list = Database.get_job_list()
        if job_list:
            for job in job_list:
                renew_by_path(job["id"], job["spider"], job["path"])
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
            start_spiders()

            while True:
                time.sleep(1)

    exit()


if __name__ == "__main__":
    main()
