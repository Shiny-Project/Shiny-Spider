# Common Header
import sys, time, json
sys.path.append('..')
from spider import Spider
from bs4 import BeautifulSoup
import requests

class BilibiliMoeSpider(Spider):
    """抓取BilibiliMoe战况"""
    api_id = '000000002'  # 声明API ID

    def __init__(self):
        super(BilibiliMoeSpider, self).__init__()  # 仅修改类名，不要修改其他

    def main(self):
        """在这里执行你的主抓取逻辑"""
        ISOTIMEFORMAT='%Y-%m-%d'
        date = str(time.strftime(ISOTIMEFORMAT, time.localtime()))
        url = 'http://moe.bilibili.com/api/s/getResult?date=' + date
        response = requests.get(url).json()["data"]
        female = dict()
        for node in response["female"] :
            female[node["id"]] = dict()
            for character in node["members"]:
                female[node["id"]][character["id"]] = dict(name = character["name"], votes_count = character["votes_count"], bangumi = character["bangumi"])
        male = dict()
        for node in response["male"] :
            male[node["id"]] = dict()
            for character in node["members"]:
                male[node["id"]][character["id"]] = dict(name = character["name"], votes_count = character["votes_count"], bangumi = character["bangumi"])
        data = dict(female = female, male = male)
        #print(data);
        result = self.createEvent(data)


if __name__ == '__main__':
    pass
