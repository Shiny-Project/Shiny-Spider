import datetime, pytz
import math
import time
import copy
from io import BytesIO

import requests
from PIL import Image

from core import spider
from lxml import etree


def in_area(point, area):
    return area[0][0] <= point[0] <= area[1][0] and area[0][1] <= point[1] <= area[1][1]


class RadarSpider(spider.Spider):
    """华东地区雷达监视"""

    def __init__(self):
        super(RadarSpider, self).__init__()
        self.name = 'Radar'

    def main(self):
        response = self.fetch('http://www.nmc.cn/publish/radar/huadong.html').decode('utf-8')
        html_tree = etree.HTML(response)
        stringify = etree.XPath("string()")
        img_url = html_tree.xpath('//*[@id="imgpath"]/@src')[0]

        # 下载读取图片
        img_response = requests.get(img_url, timeout=20).content
        image = Image.open(BytesIO(img_response)).crop((0, 0, 560, 860)).getdata()
        width, height = image.size
        pixels = list(image)

        # 需要注意的颜色列表
        warning_colors = [
            (255, 0, 0, 255),
            (214, 0, 0, 255),
            (192, 0, 0, 255),
        ]

        special_warning_colors = [
            (255, 0, 240, 255),
            (150, 0, 180, 255),
            (173, 144, 240, 255)
        ]

        # 关注的城市列表
        # 左上 右下
        cities = {
            "上海市": [
                (386, 370),
                (453, 446),
            ],
            "杭州市": [
                (295, 466),
                (363, 532),
            ],
            "郑州市": [
                (0, 220),
                (43, 267),
            ],
            # "宁波市": [
            #     (406, 466),
            #     (451, 511)
            # ],
            # "烟台市": [
            #     (314, 34),
            #     (366, 91)
            # ],
            # "济南市": [
            #     (147, 90),
            #     (193, 130)
            # ],
            # "南京市": [
            #     (266, 359),
            #     (306, 396)
            # ],
            # "福州市": [
            #     (320, 700),
            #     (363, 746)
            # ],
            # "厦门市": [
            #     (275, 796),
            #     (330, 848)
            # ],
            # "合肥市": [
            #     (185, 361),
            #     (229, 410)
            # ],
            # "武汉市": [
            #     (40, 453),
            #     (85, 489)
            # ]
        }

        # 存储的结果集
        result = {
            "上海市": 0,
            "杭州市": 0,
            "郑州市": 0,
            # "宁波市": 0,
            # "烟台市": 0,
            # "济南市": 0,
            # "南京市": 0,
            # "福州市": 0,
            # "厦门市": 0,
            # "合肥市": 0,
            # "武汉市": 0
        }

        special_warning_result = copy.copy(result)

        # 遍历像素 查找需要注意的像素点
        for index, pixel in enumerate(pixels):
            if pixel in warning_colors or pixel in special_warning_colors:
                point = (index % width, math.floor(index / width))
                for city in cities.keys():
                    if in_area(point, cities[city]):
                        # 记录这个超过阈值的点
                        if pixel in warning_colors:
                            result[city] += 1
                        else:
                            special_warning_result[cities] += 1

        # 不要太敏感。20像素再感知.
        warning_cities = []
        special_warning_cities = []

        for city in result.keys():
            if result[city] > 5:
                warning_cities.append(city)

        for city in special_warning_result.keys():
            if special_warning_result[city] > 5:
                special_warning_cities.append(city)

        if len(warning_cities) > 0:
            # 生成警告事件
            warning_text = "请下列地区注意可能到来的强对流天气:\r\n" + " ".join(warning_cities) + "。"
            warning_time = pytz.timezone('Asia/Shanghai').localize(datetime.datetime.now()).strftime('%Y-%m-%d %H')
            warning_hour = math.floor(int(warning_time.split(' ')[1]) / 6)
            warning_time = warning_time.split(' ')[0] + '#P' + str(warning_hour)

            self.record(3, {
                "title": "强对流天气警示",
                "content": warning_text,
                "link": "http://www.nmc.cn/publish/radar/huadong.html#" + warning_time
            })

        if len(special_warning_cities) > 0:
            warning_text = "下列地区检测到强雷达回波，请注意防范龙卷风、冰雹等气象灾害:\r\n" + " ".join(special_warning_cities) + "。"
            warning_time = pytz.timezone('Asia/Shanghai').localize(datetime.datetime.now()).strftime('%Y-%m-%d %H')
            warning_hour = math.floor(int(warning_time.split(' ')[1]) / 6)
            warning_time = warning_time.split(' ')[0] + '#P' + str(warning_hour)

            self.record(4, {
                "title": "强对流天气警告",
                "content": warning_text,
                "link": "http://www.nmc.cn/publish/radar/huadong.html#" + warning_time
            })
