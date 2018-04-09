from core import spider
import json
import requests


class FloodSpider(spider.Spider):
    """中国水利部水文情报预报中心"""

    def __init__(self):
        super(FloodSpider, self).__init__()
        self.name = 'Flood'

    def main(self):
        data = json.loads(requests.post(
            'http://www.hfc.gov.cn/warninfo.wrinfo/Search', data={"searchTxt": "红色"}).text)
        for item in data:
            self.record(3, {
                "title": "中国·洪水预警速报",
                "content": item["WRTitle"] + "\r\n\r\n<br><br>" + item["WRDetail"],
                "cover": item["WRIcon"],
                "link": "http://www.hfc.gov.cn" + item["Url"]
            })

    def check(self, timestamp):
        return self.check_expiration(timestamp, 180)
