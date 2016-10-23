from urllib import request
import collections
import core.database as database
from core import utils
from core.log import Log


Logger = Log()


class Spider():
    """抓取和处理数据"""
    name = 'Spider'

    def fetch(self, url):
        try:
            Logger.debug(u'试图抓取页面 [ URL = ' + url + ' ]')
            req = request.Request(url)
            req.add_header('User-Agent', 'Mirai/0.1 (https://github.com/Last-Order/Mirai-spider)')
            response = request.urlopen(req)
            Logger.debug('抓取页面 [ URL = ' + url + ' ]成功')
            return response.read()
        except Exception as e:
            Logger.error('抓取页面 [ URL = ' + url + ' ]错误:' + str(e))

    def record(self, level, data):
        if 'hash' in data:
            database.create_event(level, collections.OrderedDict(sorted(data.items())), self.name, data['hash'])
        else:
            database.create_event(level, collections.OrderedDict(sorted(data.items())), self.name, None)

    @staticmethod
    def check_expiration(timestamp, expiration):
        return utils.get_time() - timestamp <= expiration


if __name__ == '__main__':
    pass;
