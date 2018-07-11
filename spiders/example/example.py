from core import spider


class ExampleSpider(spider.Spider):
    def __init__(self, info={}):
        super(ExampleSpider, self).__init__(info)  # 仅修改类名，不要修改其他
        self.name = 'Example'  # 声明Spider名，要和类名里的一样

    def main(self):
        """主抓取逻辑，只修改内容，不修改函数名"""
        data = {
            'title': 'WUG Countdown',
            'content': self.fetch('http://wug.moe/').decode('utf-8'),
            'link': 'http://wug.moe'
        }
        # 如果 data 中不含 hash 字段，则会自动根据 data 的内容计算一个
        # 如果有，则采用

        self.record(1, data) # record(level, data) data以dict格式



if __name__ == '__main__':
    pass
