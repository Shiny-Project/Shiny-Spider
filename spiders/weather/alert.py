from core import spider
import json
import re
import time


LIST_URL = 'https://www.weather.com.cn/alarm/alarm_list.shtml'
DATA_URL = 'https://product.weather.com.cn/alarm/grepalarm_cn.php'
DETAIL_URL = 'https://product.weather.com.cn/alarm/webdata/'
CONTENT_URL = 'https://www.weather.com.cn/alarm/newalarmcontent.shtml?file='
HEADERS = {'Referer': LIST_URL}


def parse_alarminfo(content):
    # 页面通过脚本赋值加载 JSON，仅解析数据，不执行 JavaScript。
    match = re.fullmatch(
        r'\s*(?:var\s+)?alarminfo\s*=\s*(\{.*\})\s*;?\s*',
        content.decode('utf-8-sig'), re.DOTALL)
    if match is None:
        raise ValueError('中国天气网预警数据格式异常')
    return json.loads(match.group(1))


class AlertSpider(spider.Spider):
    """全国预警定点监控"""

    def __init__(self, info={}):
        super(AlertSpider, self).__init__(info)
        self.name = 'Alert'
        self.keywords = ['杭州', '上海', '郑州', '北京']
        if self.effect is not None:
            if 'temporaryWatchKeywords' in self.effect:
                self.keywords.extend(self.effect['temporaryWatchKeywords'])

    def main(self):
        data = parse_alarminfo(self.fetch(
            DATA_URL + '?_=' + str(int(time.time())), headers=HEADERS))
        for item in data['data']:
            headline = item[6]
            if '县' in headline or '区' in headline:
                continue
            if not any(keyword in headline for keyword in self.keywords):
                continue
            filename = item[1]
            detail = parse_alarminfo(self.fetch(DETAIL_URL + filename, headers=HEADERS))
            headline = detail['head']
            level = 4 if ('红色' in headline and '发布' in headline) else 3
            self.record(level, {
                "title": "中国·预警速报",
                "content": headline,
                "link": CONTENT_URL + filename,
                "alert_data": {
                    "description": detail['ISSUECONTENT'],
                    "title": headline,
                    "send_time": detail['ISSUETIME'],
                    "identifier": detail['identifier']
                }
            })

    def check(self, timestamp):
        return self.check_expiration(timestamp, 180)
