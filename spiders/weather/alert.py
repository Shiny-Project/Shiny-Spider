from core import spider
import json, time


class AlertSpider(spider.Spider):
    """全国预警定点监控"""

    def __init__(self, info={}):
        super(AlertSpider, self).__init__(info)
        self.name = 'Alert'
        self.keywords = ['杭州', '上海', '郑州', '北京']
        if self.effect is not None:
            if 'temporaryWatchKeywords' in self.effect:
                self.keywords.extend(self.effect['temporaryWatchKeywords'])

    def main(self):
        result = self.fetch("http://www.12379.cn/data/alarm_list_all.html?_=" + str(int(time.time())) ).decode("utf-8")
        data = json.loads(result)
        for item in data["alertData"]:
            for keyword in self.keywords:
                if keyword in item["headline"] and ("县" not in item["headline"] and "区" not in item["headline"]):
                    level = 4 if ("红色" in item["headline"] and "发布" in item["headline"]) else 3
                    self.record(level, {
                        "title": "中国·预警速报",
                        "content": item["headline"],
                        "link": "http://www.12379.cn/data/alarmcontent.shtml?file={}.html".format(item["identifier"]),
                        "alert_data": {
                            "description": item["description"],
                            "title": item["headline"],
                            "send_time": item["sendTime"],
                            "identifier": item["identifier"]
                        }
                    })

    def check(self, timestamp):
        return self.check_expiration(timestamp, 180)