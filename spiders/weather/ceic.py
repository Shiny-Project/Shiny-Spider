from core import spider
import json


class CEICSpider(spider.Spider):
    """中国地震台网"""

    def __init__(self):
        super(CEICSpider, self).__init__()
        self.name = 'CEIC'

    def main(self):
        result = self.fetch(
            "http://www.ceic.ac.cn/ajax/search?page=1&&start=&&end=&&jingdu1=73&&jingdu2=135&&weidu1=15&&weidu2=53&&height1=&&height2=&&zhenji1=&&zhenji2=").decode("utf-8")
        data = json.loads(result[1:-1])
        for item in data['shuju']:
            if float(item["M"]) > 5.0:
                self.record(3, {
                    "title": "中国地震速报",
                    "link": "http://news.ceic.ac.cn/" + item["NEW_DID"],
                    "content": "{time} 于 {E}E, {N}N aka. {place} 发生 {M} 地震".format(time=item["O_TIME"], E=item["EPI_LON"], N=item["EPI_LAT"], place=item["LOCATION_C"], M=item["M"]),
                    "cover": "http://maps.google.cn/maps/api/staticmap?center={N},{E}&zoom=6&size=128x128&maptype=roadmap&markers=color:red|{N},{E}&sensor=false".format(N=item["EPI_LAT"], E=item["EPI_LON"])
                })

    def check(self, timestamp):
        return self.check_expiration(timestamp, 180)
