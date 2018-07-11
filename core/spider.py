# Shiny Spider 基类

from urllib import request
import collections
import core.database as database
from core import utils
from core.log import Log
import asyncio
from aiohttp import ClientSession


Logger = Log()


class Spider():
    """抓取和处理数据"""
    name = 'Spider'
    identity = {}

    def __init__(self, info = {}):
        if 'identity' in info:
            self.identity = info['identity']

    def fetch(self, url):
        Logger.debug(u'试图抓取页面 [ URL = ' + url + ' ]')
        req = request.Request(url)
        req.add_header(
            'User-Agent', 'Shiny/0.1 (https://github.com/Shiny-Project/Shiny-README)')
        response = request.urlopen(req, timeout=10)
        Logger.debug('抓取页面 [ URL = ' + url + ' ]成功')
        return response.read()

    async def generate_fetch_tasks(self, url, session):
        async with session.get(url) as response:
            return await response.text()

    async def do_fetch_tasks(self, urls):
        async with ClientSession() as session:
            tasks = []
            for i in urls:
                Logger.debug(u'试图抓取页面 [ URL = ' + i + ' ]')
                tasks.append(asyncio.ensure_future(
                    self.generate_fetch_tasks(i, session)))
            return await asyncio.gather(*tasks)

    def fetch_many(self, urls):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.do_fetch_tasks(urls))

    def record(self, level, data):
        if 'hash' in data:
            database.create_event(level, collections.OrderedDict(
                sorted(data.items())), self.name, data['hash'])
        else:
            database.create_event(level, collections.OrderedDict(
                sorted(data.items())), self.name, None)

    def record_many(self, level, events):
        payload = []
        for event in events:
            wrappedEvent = {
                "level": level,
                "spiderName": self.name,
                "data": event
            }
            if 'channel' in event:
                wrappedEvent['channel'] = event['channel']
                event.pop('channel')
            payload.append(wrappedEvent)
        database.create_event_many(payload)

    @staticmethod
    def check_expiration(timestamp, expiration):
        return utils.get_time() - timestamp <= expiration


if __name__ == '__main__':
    pass
