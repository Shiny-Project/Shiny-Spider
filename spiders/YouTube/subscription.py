from core import spider,config
from bs4 import BeautifulSoup
import time,json

class YouTubeRSSSpider(spider.Spider):
    def __init__(self):
        super(YouTubeRSSSpider, self).__init__()  # 仅修改类名，不要修改其他
        self.name = 'YouTubeRSS'  # 声明Spider名，要和类名里的一样
        
        if config.YOUTUBE_API_KEY:
            self.YOUTUBE_API_KEY = config.YOUTUBE_API_KEY
        else:
            raise Exception('YOUTUBE_API_KEY 未指定.')

    def main(self):
        """主抓取逻辑，只修改内容，不修改函数名"""
        list = ['UUpRh2xmGtaVhFVuyCB271pw',  # Lantis
                'UU6KEU5-KSTszEOOnAl8ZwPQ',  # King Record
                'UU_A_w2KhC3emxNZWQ3pYpfQ',  # Flying Dog
                'UUeOMz8AiNhsDhEovu5_3ujQ',  # NBC
                'UUb-ekPowbBlQhyt7ZXPiu5Q',  # Pony Canyon
                'UU7RMi15o0aQacJhxOc6LLmw',  # ColumbiaMusicJp
                'UUUzpZpX2wRYOk3J8QTFGxDg',  # 乃木坂 46 OFFICIAL
                'UUmr9bYmymcBmQ1p2tLBRvwg',  # 欅坂46 OFFICIAL
                'UUCy_q-N7F2FOIZ6ZggHIAKg',  # Sony Music (Japan)
                ]
        for up in list:
            url = 'https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId=' + up + '&key=' + self.YOUTUBE_API_KEY
            text = self.fetch(url).decode('utf-8')
            res = json.loads(text)
            for item in res["items"]:
                title = item["snippet"]["title"]
                cover = item["snippet"]["thumbnails"]["default"]["url"]
                description = item["snippet"]["description"]
                link = "https://www.youtube.com/watch?v=" + item["snippet"]["resourceId"]["videoId"]
                self.record(3, {
                    "title": title,
                    "link": link,
                    "content": description,
                    "cover": cover
                })

    def check(self, timestamp):  # 这个函数可以不写
        """检查数据是否过期(optional)，只修改内容，不修改函数名，返回布尔型"""
        return self.check_expiration(timestamp, 60)


if __name__ == '__main__':
    pass
