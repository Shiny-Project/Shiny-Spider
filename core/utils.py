import importlib.util
import time


def load_spider(path):
    # 面向StackOverflow编程抄来的代码 根据路径导入包
    spec = importlib.util.spec_from_file_location("Mirai", './spiders/' + path + '.py')
    spider = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(spider)
    return spider


def parse_time_string(time_string):
    try:
        timestamp = int(time.mktime(time_string.timetuple()))
        return timestamp
    except Exception as e:
        return 0


def get_time():
    return int(time.time())
