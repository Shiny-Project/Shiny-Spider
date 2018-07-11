from core import spider
from bs4 import BeautifulSoup
import re


class USGSEarthquakeSpider(spider.Spider):
    def __init__(self, info={}):
        super(USGSEarthquakeSpider, self).__init__(info)  # 仅修改类名，不要修改其他
        self.name = 'USGSEarthquake'  # 声明Spider名，要和类名里的一样

    def main(self):
        """主抓取逻辑，只修改内容，不修改函数名"""
        data = self.fetch('http://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_week.atom').decode(
            'utf-8')
        soup = BeautifulSoup(data, 'xml')
        latest = soup.find_all('entry')

        if latest:
            latest = latest[0]
            level = int(
                re.search('M (\d)\.\d', latest.title.get_text()).group(1))
            link = latest.link.get('href')
            title = "USGS地震速报"
            content = latest.title.get_text()
            location = latest.find('georss:point').get_text()
            depth = latest.find('georss:elev').get_text()
            self.record(level - 3, {
                "title": title,
                "link": link,
                "content": content,
                "cover": "",
                "location": location,
                "depth": depth
            })


if __name__ == '__main__':
    pass
