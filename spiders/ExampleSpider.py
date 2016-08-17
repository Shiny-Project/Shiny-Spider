# Common Header
from bs4 import BeautifulSoup

from .. import spider


class ExampleSpider(spider.Spider):
    """Spider描述"""
    name = 'Example'  # 声明Spider名

    def __init__(self):
        super(ExampleSpider, self).__init__()  # 仅修改类名，不要修改其他

    def main(self):
        """在这里执行你的主抓取逻辑"""
        url = 'http://www.wz121.com/WeatherForecast/ThreeHourForecast.htm'
        response = self.fetch(url)
        html = BeautifulSoup(response, "html.parser", from_encoding="utf-8")
        node = html.find(attrs={"id": 'ctl00_ContentBody_newsContent'})
        data = dict(forecast=node.text)
        result = self.createEvent(data)


if __name__ == '__main__':
    pass
