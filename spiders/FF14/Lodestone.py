from core import spider
from lxml import etree


class LodestoneSpider(spider.Spider):
    """ Final Fantasy Lodestone Topic Spider """

    def __init__(self, socket):
        super(LodestoneSpider, self).__init__(socket)
        self.name = 'Lodestone'

    def main(self):
        """" 抓取逻辑 """
        response = self.fetch(
            "http://jp.finalfantasyxiv.com/lodestone/topics/").decode('utf-8')
        html_tree = etree.HTML(response)
        stringify = etree.XPath("string()")
        title = stringify(html_tree.xpath(
            '//*[@id="main"]/div/div[2]/ul/li[1]/header/span/a')[0])
        content = stringify(html_tree.xpath(
            '//*[@id="main"]/div/div[2]/ul/li[1]/div')[0])
        link = 'http://jp.finalfantasyxiv.com' + \
            html_tree.xpath(
                '//*[@id="main"]/div/div[2]/ul/li[1]/div/a[1]/@href')[0]
        self.record(3, {
            "title": title,
            "content": content
        })
