from core import spider
from bs4 import BeautifulSoup


# fripSide新闻监视
class fripSideSpider(spider.Spider):

    def __init__(self, info={}):
        super(fripSideSpider, self).__init__(info)  # 仅修改类名，不要修改其他
        self.name = 'fripSide'  # 声明Spider名，要和类名里的一样

    def main(self):
        """主抓取逻辑，只修改内容，不修改函数名"""
        text = self.fetch(
            'http://nbcuni-music.com/fripside/rss/news/rss2_0001.xml').decode('utf-8')
        soup = BeautifulSoup(text, 'xml')
        lastest = soup.find_all('item')[0]
        title = lastest.title.get_text()
        link = lastest.link.get_text()
        content = lastest.description.get_text()
        self.record(3, {
            "title": title,
            "content": content,
            "link": link
        })


if __name__ == '__main__':
    pass
