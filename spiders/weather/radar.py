import datetime
import math
import time
from io import BytesIO

import requests
from PIL import Image

from core import spider
from lxml import etree


class RadarSpider(spider.Spider):
    """华东地区雷达监视"""
    def __init__(self):
        super(RadarSpider, self).__init__()
        self.name = 'RadarSpider'

    def main(self):
        response = self.fetch('http://www.nmc.cn/publish/radar/huadong.html').decode('utf-8')
        html_tree = etree.HTML(response)
        stringify = etree.XPath("string()")
        img_url = html_tree.xpath('//*[@id="imgpath"]/@src')[0]

        # 下载读取图片
        img_response = requests.get(img_url).content
        image = Image.open(BytesIO(img_response)).crop((0, 0, 560, 860)).getdata()
        width, height = image.size
        pixels = list(image)

        # 需要注意的颜色列表
        warning_colors = [
            (255, 0, 0, 255),
            (214, 0, 0, 255),
            (192, 0, 0, 255),
            (255, 0, 240, 255),
            (150, 0, 180, 255),
            (173, 144, 240, 255)
        ]

        # 关注的城市列表
        # 左上 右上 右下 左下
        citys = {
            "上海市": [
                (386, 370),
                (453, 370),
                (453, 446),
                (386, 446)
            ],
            "杭州市": [
                (295, 466),
                (363, 466),
                (363, 532),
                (295, 532)
            ],
            "郑州市": [
                (0, 220),
                (43, 220),
                (43, 267),
                (0, 267)
            ]
        }
        
        # 存储的结果集
        result = {
            "上海市": 0,
            "杭州市": 0,
            "郑州市": 0
        }

        # 遍历像素 查找需要注意的像素点
        for index, pixel in enumerate(pixels):
            if pixel in warning_colors:
                point = (index % width, math.floor(index / width))
                for city in citys.keys():
                    if in_area(point, citys[city]):
                        # 记录这个超过阈值的点
                        result[city] += 1
        
        # 不要太敏感。20像素再感知.
        warning_citys = []
        for city in result.keys():
            if result[city] > 20:
                warning_citys.append(city)
        
        if len(warning_citys) > 0:
            # 生成警告事件
            warning_text = "请下列地区注意可能到来的强对流天气:\r\n" + " ".join(warning_citys) + "。"
            warning_time = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H')
            warning_hour = math.floor(int(warning_time.split(' ')[1]) / 6)
            warning_time = warning_time.split(' ')[0] + '#P' + str(warning_hour)

            self.record(3, {
                "title": "强对流天气警示",
                "content": warning_text,
                "link": "http://www.nmc.cn/publish/radar/huadong.html#" + warning_time
            })
        else:
            pass