# Shiny 数据库通讯

import hashlib
import json

import core.config as config
from core.log import Log
from core import meta

import Shiny

# Shiny SDK
shiny = Shiny.Shiny(config.API_KEY, config.API_SECRET_KEY, spider_version=meta.version, api_host='http://localhost:1337')

# 创建日志类
Logger = Log()


def create_event(level, data, name, hash):
    """记录数据"""
    if not hash:
        m = hashlib.md5()
        event = json.dumps(data).encode('utf-8')
        m.update(event)
        hash = m.hexdigest()

    try:
        shiny.add(name, level, data, hash=hash)
        Logger.info(
            '[ Spider = ' + name + ' ] 数据已经提交 [ Hash = ' + hash + ' ]')
    except Shiny.ShinyError as e:
        Logger.error('无法向Shiny提交数据:' + str(e))
    except Exception as e:
        Logger.error('无法记录数据' + str(e))


def create_event_many(events):
    """记录多个数据"""
    try:
        result = shiny.add_many(events)
        Logger.info("多个事件数据已经提交 其中 {}/{} 是新事件已被记录".format(len(result["data"]), len(events)))
    except Shiny.ShinyError as e:
        Logger.error("无法向 Shiny 提交数据 / 网络错误" + str(e))
    except Exception as e:
        Logger.error("无法向 Shiny 提交数据" + str(e))


def get_job_list():
    """获得全部 Spider 列表"""
    try:
        response = shiny.get_jobs()
        return response["data"]
    except Exception as e:
        Logger.error('无法获得 Spider 列表' + str(e))


def report_job_status(job_id, status):
    """ 报告任务状态 """
    try:
        response = shiny.report(job_id, status)
        Logger.debug("回报任务状态 [ ID " + str(job_id) + " = " + status + " ]")
    except Exception as e:
        Logger.error('回报任务状态失败' + str(e))
