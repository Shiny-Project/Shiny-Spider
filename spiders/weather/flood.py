from core import spider
import json
import requests


class FloodSpider(spider.Spider):
    """中国水利部水文情报预报中心"""

    def __init__(self, info={}):
        super(FloodSpider, self).__init__(info)
        self.name = 'Flood'

    def parse_influenced_areas(self, text):
        result = {}
        if "：" in text:
            # 省级以下细分
            if ";" in text:
                # 多省多区域
                # Example："河南省：三门峡市;陕西省：西安市、渭南市"
                for province in text.split(';'):
                    result[province.split('：')[0]] = province.split('：')[1].split('、')
            else:
                # 单省多区域
                # Example："甘肃省：舟曲县"
                result[text.split('：')[0]] = [text.split('：')[1].split(';')]
        else:
            # 省级以下不细分
            # Example: "河南省;湖北省;湖南省;重庆市;四川省;云南省;陕西省;甘肃省;青海省"
            result["national"] = text.split(';')
        return result

    def main(self):
        data = json.loads(requests.post(
            'http://www.hfc.gov.cn/warninfo.wrinfo/mapdata', data={
                "wrtype": "洪水",
                "wrlevel": "All"
            }).text)
        icon_map = {
            "蓝色": "https://shiny-push.oss-ap-southeast-1.aliyuncs.com/FLOOD_ALERT_BLUE.png",
            "黄色": "https://shiny-push.oss-ap-southeast-1.aliyuncs.com/FLOOD_ALERT_YELLOW.png",
            "橙色": "https://shiny-push.oss-ap-southeast-1.aliyuncs.com/FLOOD_ALERT_ORANGE.png",
            "红色": "https://shiny-push.oss-ap-southeast-1.aliyuncs.com/FLOOD_ALERT_RED.png"
        }
        for item in data:
            if item["UnitID"] == "01":
                # 水利部 全国范围 
                self.record(3, {
                    "title": "中国·洪水预警速报",
                    "content": item["WRTitle"] + "\r\n\r\n" + item["WRDetail"],
                    "cover": icon_map[item["WRLevel"]],
                    "link": "http://www.hfc.gov.cn" + item["Url"],
                    "issueUnit": item["UnitID"],
                    "issueUnitText": item["UnitName"],
                    "floodAlertTitle": item["WRTitle"],
                    "floodAlertDetail": item["WRDetail"],
                    "floodAlertLevel": item["WRLevel"],
                    "influencedAreas": self.parse_influenced_areas(item["InfluadArea"])
                })
            elif item["WRLevel"] == "橙色" or item["WRLevel"] == "红色":
                # 橙色 红色预警
                  self.record(3, {
                    "title": "中国·洪水预警速报",
                    "content": item["WRTitle"] + "\r\n\r\n" + item["WRDetail"],
                    "cover": icon_map[item["WRLevel"]],
                    "link": "http://www.hfc.gov.cn" + item["Url"],
                    "issueUnit": item["UnitID"],
                    "issueUnitText": item["UnitName"],
                    "floodAlertTitle": item["WRTitle"],
                    "floodAlertDetail": item["WRDetail"],
                    "floodAlertLevel": item["WRLevel"],
                    "influencedAreas": self.parse_influenced_areas(item["InfluadArea"])
                })
            else:
                pass

    def check(self, timestamp):
        return self.check_expiration(timestamp, 180)
