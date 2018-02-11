# Shiny 数据库通讯

import datetime, hashlib, time
import json

import core.config as config
from core import utils
from core.log import Log

import Shiny

# Shiny SDK
shiny = Shiny.Shiny(config.API_KEY, config.API_SECRET_KEY)

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
        try:
            shiny.add(name, level, data, hash=hash)
            Logger.info('[ Spider = ' + name + ' ] 新的数据已经记录 [ Hash = ' + hash + ' ]')
        except Shiny.ShinyError as e:
            Logger.error('无法向Shiny提交数据:' + str(e))

    except Exception as e:
        Logger.error('无法记录数据' + str(e))

class Database():
    def get_job_list(self):
        """获得全部 Spider 列表"""
        try:
            response = shiny.get_jobs()
            return response["data"]
        except Exception as e:
            Logger.error('无法获得 Spider 列表' + str(e))
    
    def report_job_status(self, job_id, status):
        """ 报告任务状态 """
        try:
            response = shiny.report(job_id, status)
            Logger.debug("回报任务状态 [ ID " + str(job_id) + " = " + status + " ]")
        except Exception as e:
            Logger.error('回报任务状态失败' + str(e))