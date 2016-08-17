import hashlib
import json
import time
from urllib import request

import database
from log import Log

Logger = Log()


class Spider():
    """抓取和处理数据"""

    def __init__(self):
        pass

    def fetch(self, url):
        try:
            Logger.debug(u'试图抓取页面[ URL = ' + url + ' ]')
            req = request.Request(url)
            req.add_header('User-Agent', 'Mirai/0.1 (https://github.com/Last-Order/Mirai-spider)')
            response = request.urlopen(req)
            Logger.debug('抓取页面[ URL = ' + url + ' ]成功')
            return response.read()
        except Exception as e:
            Logger.error('抓取页面[ URL = ' + url + ' ]错误:' + str(e))

    def generate_event_id(data):
        m = hashlib.md5()
        event = (str(data) + str(time.ctime())).encode('utf-8')
        m.update(event)
        return m.hexdigest()

    def create_event(self, name, data):
        event_id = self.generate_event_id(data)
        return database.addEvent(event_id, name, json.JSONEncoder().encode(data))


if __name__ == '__main__':
    pass;
