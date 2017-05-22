from core import spider
from lxml import etree


class LodestoneSpider(spider.Spider):
    """ Final Fantasy Lodestone Topic Spider """

    def __init__(self):
        super(LodestoneSpider, self).__init__()
        self.name = 'Lodestone'

    def main(self):
        """" 抓取逻辑 """
        response = self.fetch(
            "http://jp.finalfantasyxiv.com/lodestone/topics/").decode('utf-8')
        html_tree = etree.HTML(response)
        stringify = etree.XPath("string()")
        title = stringify(html_tree.xpath(
            '//*[@id="news"]/div[4]/div[2]/div[1]/div/ul[3]/li[1]/header/p/a')[0])
        content = stringify(html_tree.xpath(
            '//*[@id="news"]/div[4]/div[2]/div[1]/div/ul[3]/li[1]/div/p[2]')[0])
        link = 'http://jp.finalfantasyxiv.com' + \
            html_tree.xpath(
                '//*[@id="news"]/div[4]/div[2]/div[1]/div/ul[3]/li[1]/header/p/a/@href')[0]
        self.record(3, {
            "title": title,
            "content": content,
            "link": link
        })
