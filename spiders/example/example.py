from core import spider


class ExampleSpider(spider.Spider):
    def __init__(self, socket):
        super(ExampleSpider, self).__init__(socket)  # 仅修改类名，不要修改其他
        self.name = 'Example'  # 声明Spider名，要和类名里的一样

    def main(self):
        """主抓取逻辑，只修改内容，不修改函数名"""
        data = {
            'title': 'WUG Countdown',
            'content': self.fetch('http://wug.moe/').decode('utf-8'),
            'link': 'http://wug.moe'
        }

        self.record(1, data) # record(level, data) data以dict格式

    def check(self, timestamp): # 这个函数可以不写
        """检查数据是否过期(optional)，只修改内容，不修改函数名，返回布尔型"""
        return self.check_expiration(timestamp, 5) # 快速判断数据是否过时，第二个参数的单位是秒


if __name__ == '__main__':
    pass
