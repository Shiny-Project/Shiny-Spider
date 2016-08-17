import database
from urllib import request

from log import Log

Logger = Log()


class Spider():
    """抓取和处理数据"""
    name = 'Spider'

    def __init__(self):
        pass

    def fetch(self, url):
        try:
            Logger.debug(u'试图抓取页面 [ URL = ' + url + ' ]')
            req = request.Request(url)
            req.add_header('User-Agent', 'Mirai/0.1 (https://github.com/Last-Order/Mirai-spider)')
            response = request.urlopen(req)
            Logger.info('抓取页面 [ URL = ' + url + ' ]成功')
            return response.read()
        except Exception as e:
            Logger.error('抓取页面 [ URL = ' + url + ' ]错误:' + str(e))

    def record(self, level, data):
        database.create_event(level, data, self.name)




if __name__ == '__main__':
    pass;
