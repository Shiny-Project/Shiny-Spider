import json

from core import spider


class ExampleSpider(spider.Spider):
    def __init__(self):
        super(ExampleSpider, self).__init__()  # 仅修改类名，不要修改其他
        self.name = 'Example'  # 声明Spider名

    def main(self):
        """主抓取逻辑，只修改内容，不修改函数名"""
        data = json.dumps({
            'page': self.fetch('http://wug.moe/').decode('utf-8')
        })

        self.record(1, data)

    def check(self, timestamp):
        """检查数据是否过期(optional)，只修改内容，不修改函数名，返回布尔型"""
        return self.check_expiration(timestamp, 60)


if __name__ == '__main__':
    pass
