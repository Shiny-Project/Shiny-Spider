import spider


class ExampleSpider(spider.Spider):
    def __init__(self):
        super(ExampleSpider, self).__init__()  # 仅修改类名，不要修改其他

    def main(self):
        print('Call to example spider')


if __name__ == '__main__':
    pass
