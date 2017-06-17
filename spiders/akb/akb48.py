from core import spider
import json

class AKB48Spider(spider.Spider):
    def __init__(self):
        super(AKB48Spider, self).__init__()  # 仅修改类名，不要修改其他
        self.name = 'AKB48'  # 声明Spider名，要和类名里的一样

    def main(self):
        """主抓取逻辑，只修改内容，不修改函数名"""
        data = self.fetch("http://www.akb48.co.jp/sousenkyo49th/result").decode('utf-8')
        data = json.loads(data)
        for member in data["selection_member"]:
            data = {
                'title': 'AKB 49th 总选举第 ' + member["rank"] + " 位",
                'content': member["group_name"] + ' ' + member["team_name"] + ' ' + member["name1"] + ' ' + member["vote_number"],
                'link': 'http://www.akb48.co.jp/sousenkyo49th',
                'cover': member['image_url']
            }
            self.record(3, data)
    

    def check(self, timestamp): # 这个函数可以不写
        """检查数据是否过期(optional)，只修改内容，不修改函数名，返回布尔型"""
        return self.check_expiration(timestamp, 5) # 快速判断数据是否过时，第二个参数的单位是秒


if __name__ == '__main__':
    pass
