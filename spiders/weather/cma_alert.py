from core import spider
from bs4 import BeautifulSoup
import datetime, pytz, time


def class_is_warning(css_class=[]):
    if css_class is None:
        return False
    return 'warning' in css_class


class CMAAlertSpider(spider.Spider):
    """CMA预警速报"""

    def __init__(self):
        super(CMAAlertSpider, self).__init__()
        self.name = 'CMAAlert'

    def main(self):
        result = self.fetch("http://www.nmc.cn/").decode('utf-8')
        soup = BeautifulSoup(result)
        warning_list = soup.find_all('li', class_='waring')
        tz = pytz.timezone('Asia/Shanghai')
        if len(warning_list) > 0:
            for item in soup.find_all('li', class_='waring')[0].find_all('a'):
                if '蓝色' in item.attrs['title'] or '黄色' in item.attrs['title']:
                    self.record(3, {
                        "title": "CMA·全国级预警速报",
                        "link": 'http://www.nmc.cn' + item.attrs['href'],
                        "content": item.attrs['title'] + '(' + datetime.datetime.fromtimestamp(int(time.time()), tz).strftime('%Y-%m-%d') + ')'
                    })
                if '橙色' in item.attrs['title'] or '红色' in item.attrs['title']:
                    if '解除' in item.attrs['title']:
                        self.record(3, {
                            "title": "CMA·全国级预警速报",
                            "link": "http://www.nmc.cn" + item.attrs['href'],
                            "content": item.attrs['title'] + '(' + datetime.datetime.fromtimestamp(int(time.time()), tz).strftime('%Y-%m-%d') + ')'
                        })
                    else:
                        self.record(4, {
                            "title": "CMA·全国级预警速报",
                            "link": "http://www.nmc.cn" + item.attrs['href'],
                            "content": item.attrs['title'] + '(' + datetime.datetime.fromtimestamp(int(time.time()), tz).strftime('%Y-%m-%d') + ')'
                        })

    def check(self, timestamp):
        return self.check_expiration(timestamp, 180)
