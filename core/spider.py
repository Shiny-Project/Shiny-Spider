# Shiny Spider 基类

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
        Logger.debug(u'试图抓取页面 [ URL = ' + url + ' ]')
        req = request.Request(url)
        req.add_header('User-Agent', 'Shiny/0.1 (https://github.com/Shiny-Project/Shiny-README)')
        response = request.urlopen(req, timeout=10)
        Logger.debug('抓取页面 [ URL = ' + url + ' ]成功')
        return response.read()

    def record(self, level, data):
        if 'hash' in data:
            database.create_event(level, collections.OrderedDict(sorted(data.items())), self.name, data['hash'])
        else:
            database.create_event(level, collections.OrderedDict(sorted(data.items())), self.name, None)

    @staticmethod
    def check_expiration(timestamp, expiration):
        return utils.get_time() - timestamp <= expiration


if __name__ == '__main__':
    pass
