from core import spider
from bs4 import BeautifulSoup


def class_is_even_or_odd(css_class=[]):
    if css_class is None:
        return False
    return 'even' in css_class or 'odd' in css_class


class AlertSpider(spider.Spider):
    """CMA 全国气象预警"""

    def __init__(self):
        super(AlertSpider, self).__init__()
        self.name = 'AlertSpider'

    def main(self):
        text = self.fetch('http://www.nmc.cn/f/alarm.html').decode('utf-8')
        tree = BeautifulSoup(text, 'xml')
        alert_list = tree.find_all('div', class_=class_is_even_or_odd)
        for alert in alert_list:
            if ("上海" in alert.a.text or "杭州" in alert.a.text or "郑州" in alert.a.text) and ("市气象台" in alert.a.text) and ("区" not in alert.a.text and "县" not in alert.a.text):
                self.record(3, {
                    "title": "中国·气象预警速报",
                    "link": "http://www.nmc.cn" + alert.a.get('href'),
                    "content": alert.find(class_="date").text + " " + alert.a.text,
                    "cover": alert.img.get('src')
                })

    def check(self, timestamp):
        return self.check_expiration(timestamp, 180)
