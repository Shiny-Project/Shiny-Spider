from core import spider
from lxml import etree


class LLSSNewsSpider(spider.Spider):
    def __init__(self):
        super(LLSSNewsSpider, self).__init__()  # 仅修改类名，不要修改其他
        self.name = 'LLSSNews'  # 声明Spider名，要和类名里的一样

    def main(self):
        """主抓取逻辑，只修改内容，不修改函数名"""

        url = 'http://www.lovelive-anime.jp/uranohoshi/news.php'
        html = self.fetch(url).decode('utf-8')
        selector = etree.HTML(html)
        news = selector.xpath('//*[@id="contents"]/div')

        #check news
        for element in news:
            ids = element.xpath('@id')
            id = ids[0]
            titles = element.xpath('div[1]/div/text()')
            title = titles[0]
            pageurl = url + "#" + id
            contents = element.xpath('p/text()')
            content = '\n'.join(contents)
            innerHtml = etree.tostring(element)

            json_data = {
                "title": title,
                "content": content.strip(),
                "link": pageurl,
                "cover": "https://zyzsdy-com-static.smartgslb.com/Public/img/sunshine_logo.png"
            }

            self.record(3, json_data) # record(level, data) data以dict格式



if __name__ == '__main__':
    pass
