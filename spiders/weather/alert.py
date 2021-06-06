from core import spider
import json, time


class AlertSpider(spider.Spider):
    """全国预警定点监控"""

    def __init__(self, info={}):
        super(AlertSpider, self).__init__(info)
        self.name = 'Alert'

    def main(self):
        result = self.fetch("http://www.12379.cn/data/alarm_list_all.html?_=" + str(int(time.time())) ).decode("utf-8")
        data = json.loads(result)
        for item in data["alertData"]:
            if ("杭州" in item["headline"] or "上海" in item["headline"] or "郑州" in item["headline"]) and ("县" not in item["headline"] and "区" not in item["headline"]):
                if ("红色" in item["headline"] and "发布" in item["headline"]):
                    self.record(4, {
                        "title": "中国·预警速报",
                        "content": item["headline"],
                        "link": "http://www.12379.cn/data/alarmcontent.shtml?file={}.html".format(item["identifier"])
                    })
                else:
                    self.record(3, {
                        "title": "中国·预警速报",
                        "content": item["headline"],
                        "link": "http://www.12379.cn/data/alarmcontent.shtml?file={}.html".format(item["identifier"])
                    })

    def check(self, timestamp):
        return self.check_expiration(timestamp, 180)