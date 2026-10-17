# Shiny Helper Functions

import importlib
import time,datetime


def load_spider(path):
    # 按模块路径加载并复用模块，保留爬虫跨轮调度的内存状态。
    return importlib.import_module('spiders.' + path.replace('/', '.'))

def parse_time_string(time_string):
    try:
        timestamp = int(time.mktime(time_string.timetuple()))
        return timestamp
    except Exception as e:
        return 0

def get_time():
    return int(time.time())

def get_timestamp():
    return datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
