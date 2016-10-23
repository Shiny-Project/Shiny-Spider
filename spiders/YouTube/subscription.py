from core import spider
from bs4 import BeautifulSoup


class YouTubeRSSSpider(spider.Spider):
    def __init__(self):
        super(YouTubeRSSSpider, self).__init__()  # 仅修改类名，不要修改其他
        self.name = 'YouTubeRSS'  # 声明Spider名，要和类名里的一样

    def main(self):
        """主抓取逻辑，只修改内容，不修改函数名"""
        list = ['https://www.youtube.com/feeds/videos.xml?channel_id=UCpRh2xmGtaVhFVuyCB271pw',  # Lantis
                'https://www.youtube.com/feeds/videos.xml?channel_id=UC6KEU5-KSTszEOOnAl8ZwPQ',  # King Record
                'https://www.youtube.com/feeds/videos.xml?channel_id=UC_A_w2KhC3emxNZWQ3pYpfQ',  # Flying Dog
                'https://www.youtube.com/feeds/videos.xml?channel_id=UCeOMz8AiNhsDhEovu5_3ujQ',  # NBC
                'https://www.youtube.com/feeds/videos.xml?channel_id=UCb-ekPowbBlQhyt7ZXPiu5Q'  # Pony Canyon
                ]
        for up in list:
            text = self.fetch(up).decode(
                'utf-8')
            soup = BeautifulSoup(text, 'xml')
            lastest = soup.find_all('entry')[0]
            link = lastest.link.get('href')
            detail = lastest.find('group')
            title = detail.title.get_text()
            description = detail.description.get_text()
            cover = detail.thumbnail.get('url')
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
