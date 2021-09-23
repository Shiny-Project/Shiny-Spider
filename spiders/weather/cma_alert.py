from core import spider
from bs4 import BeautifulSoup
import datetime
import re
import pytz
import time


def class_is_warning(css_class=[]):
    if css_class is None:
        return False
    return 'warning' in css_class


class CMAAlertSpider(spider.Spider):
    """CMA预警速报"""

    def __init__(self, info={}):
        super(CMAAlertSpider, self).__init__(info)
        self.name = 'CMAAlert'

    def parse_alert(self, alert_name):
        alert_data = {
            "台风蓝色": {
                "icon": "https://upload.wikimedia.org/wikipedia/commons/5/5b/Blue_typhoon_alert_-_China.svg",
                "description": "24小时内可能或者已经受热带气旋影响，沿海或者陆地平均风力达6级以上，或者阵风8级以上并可能持续。"
            },
            "台风黄色": {
                "icon": "https://upload.wikimedia.org/wikipedia/commons/8/80/Yellow_typhoon_alert_-_China.svg",
                "description": "24小时内可能或者已经受热带气旋影响，沿海或者陆地平均风力达8级以上，或者阵风10级以上并可能持续。"
            },
            "台风橙色": {
                "icon": "https://upload.wikimedia.org/wikipedia/commons/7/75/Orange_typhoon_alert_-_China.svg",
                "description": "12小时内可能或者已经受热带气旋影响，沿海或者陆地平均风力达10级以上，或者阵风12级以上并可能持续。"
            },
            "台风红色": {
                "icon": "https://upload.wikimedia.org/wikipedia/commons/f/fc/Red_typhoon_alert_-_China.svg",
                "description": "6小时内可能或者已经受热带气旋影响，沿海或者陆地平均风力达12级以上，或者阵风达14级以上并可能持续。"
            },
            "暴雨蓝色": {
                "icon": "https://upload.wikimedia.org/wikipedia/commons/d/dd/Blue_rain_storm_alert_-_China.svg",
                "description": "12小时内降雨量将达50毫米以上，或者已达50毫米以上且降雨可能持续。"
            },
            "暴雨黄色": {
                "icon": "https://upload.wikimedia.org/wikipedia/commons/b/b9/Yellow_rain_storm_alert_-_China.svg",
                "description": "6小时内降雨量将达50毫米以上，或者已达50毫米以上且降雨可能持续。"
            },
            "暴雨橙色": {
                "icon": "https://upload.wikimedia.org/wikipedia/commons/7/79/Orange_rain_storm_alert_-_China.svg",
                "description": "3小时内降雨量将达50毫米以上，或者已达50毫米以上且降雨可能持续。"
            },
            "暴雨红色": {
                "icon": "https://upload.wikimedia.org/wikipedia/commons/8/84/Red_rain_storm_alert_-_China.svg",
                "description": "3小时内降雨量将达100毫米以上，或者已达100毫米以上且降雨可能持续。"
            },
            "暴雪蓝色": {
                "icon": "https://upload.wikimedia.org/wikipedia/commons/a/a9/Blue_snow_storm_alert_-_China.svg",
                "description": "12小时内降雪量将达4毫米以上，或者已达4毫米以上且降雪持续，可能对交通或者农牧业有影响。"
            },
            "暴雪黄色": {
                "icon": "https://upload.wikimedia.org/wikipedia/commons/4/4c/Yellow_snow_storm_alert_-_China.svg",
                "description": "12小时内降雪量将达6毫米以上，或者已达6毫米以上且降雪持续，可能对交通或者农牧业有影响。"
            },
            "暴雪橙色": {
                "icon": "https://upload.wikimedia.org/wikipedia/commons/3/3a/Orange_snow_storm_alert_-_China.svg",
                "description": "6小时内降雪量将达10毫米以上，或者已达10毫米以上且降雪持续，可能或者已经对交通或者农牧业有较大影响。"
            },
            "暴雪红色": {
                "icon": "https://upload.wikimedia.org/wikipedia/commons/9/9c/Red_snow_storm_alert_-_China.svg",
                "description": "6小时内降雪量将达15毫米以上，或者已达15毫米以上且降雪持续，可能或者已经对交通或者农牧业有较大影响。"
            },
            "寒潮蓝色": {
                "icon": "https://upload.wikimedia.org/wikipedia/commons/a/aa/Blue_cold_wave_alert_-_China.svg",
                "description": "48小时内最低气温将要下降8℃以上，最低气温小于等于4℃，陆地平均风力可达5级以上；或者已经下降8℃以上，最低气温小于等于4℃，平均风力达5级以上，并可能持续。"
            },
            "寒潮黄色": {
                "icon": "https://upload.wikimedia.org/wikipedia/commons/4/47/Yellow_cold_wave_alert_-_China.svg",
                "description": "24小时内最低气温将要下降10℃以上，最低气温小于等于4℃，陆地平均风力可达6级以上；或者已经下降10℃以上，最低气温小于等于4℃，平均风力达6级以上，并可能持续。"
            },
            "寒潮橙色": {
                "icon": "https://upload.wikimedia.org/wikipedia/commons/d/dc/Orange_cold_wave_alert_-_China.svg",
                "description": "24小时内最低气温将要下降12℃以上，最低气温小于等于0℃，陆地平均风力可达6级以上；或者已经下降12℃以上，最低气温小于等于0℃，平均风力达6级以上，并可能持续。"
            },
            "寒潮红色": {
                "icon": "https://upload.wikimedia.org/wikipedia/commons/a/a5/Red_cold_wave_alert_-_China.svg",
                "description": "24小时内最低气温将要下降16℃以上，最低气温小于等于0℃，陆地平均风力可达6级以上；或者已经下降16℃以上，最低气温小于等于0℃，平均风力达6级以上，并可能持续。"
            },
            "大风蓝色": {
                "icon": "https://upload.wikimedia.org/wikipedia/commons/a/a0/Blue_gale_alert_-_China.svg",
                "description": "24小时内可能受大风影响,平均风力可达6级以上，或者阵风7级以上；或者已经受大风影响,平均风力为6～7级，或者阵风7～8级并可能持续。"
            },
            "大风黄色": {
                "icon": "https://upload.wikimedia.org/wikipedia/commons/a/a9/Yellow_gale_alert_-_China.svg",
                "description": "12小时内可能受大风影响,平均风力可达8级以上，或者阵风9级以上；或者已经受大风影响,平均风力为8～9级，或者阵风9～10级并可能持续。"
            },
            "大风橙色": {
                "icon": "https://upload.wikimedia.org/wikipedia/commons/7/72/Orange_gale_alert_-_China.svg",
                "description": "6小时内可能受大风影响,平均风力可达10级以上，或者阵风11级以上；或者已经受大风影响,平均风力为10～11级，或者阵风11～12级并可能持续。"
            },
            "大风红色": {
                "icon": "https://upload.wikimedia.org/wikipedia/commons/9/93/Red_gale_alert_-_China.svg",
                "description": "6小时内可能受大风影响，平均风力可达12级以上，或者阵风13级以上；或者已经受大风影响，平均风力为12级以上，或者阵风13级以上并可能持续。"
            },
            "沙尘暴黄色": {
                "icon": "https://upload.wikimedia.org/wikipedia/commons/1/16/Yellow_sand_storm_alert_-_China.svg",
                "description": "12小时内可能出现沙尘暴天气（能见度小于1000米），或者已经出现沙尘暴天气并可能持续。"
            },
            "沙尘暴橙色": {
                "icon": "https://upload.wikimedia.org/wikipedia/commons/c/c8/Orange_sand_storm_alert_-_China.svg",
                "description": "6小时内可能出现强沙尘暴天气（能见度小于500米），或者已经出现强沙尘暴天气并可能持续。",
            },
            "沙尘暴红色": {
                "icon": "https://upload.wikimedia.org/wikipedia/commons/e/e6/Red_sand_storm_alert_-_China.svg",
                "description": "6小时内可能出现特强沙尘暴天气（能见度小于50米），或者已经出现特强沙尘暴天气并可能持续。"
            },
            "高温黄色": {
                "icon": "https://upload.wikimedia.org/wikipedia/commons/2/2a/Yellow_heat_wave_alert_-_China.svg",
                "description": "连续三天日最高气温将在35℃以上。"
            },
            "高温橙色": {
                "icon": "https://upload.wikimedia.org/wikipedia/commons/0/0c/Orange_heat_wave_alert_-_China.svg",
                "description": "24小时内最高气温将升至37℃以上。"
            },
            "高温红色": {
                "icon": "https://upload.wikimedia.org/wikipedia/commons/f/f2/Red_heat_wave_alert_-_China.svg",
                "description": "24小时内最高气温将升至40℃以上。"
            },
            "干旱橙色": {
                "icon": "https://upload.wikimedia.org/wikipedia/commons/5/5c/Orange_drought_alert_-_China.svg",
                "description": "预计未来一周综合气象干旱指数达到重旱（气象干旱为25～50年一遇），或者某一县（区）有40%以上的农作物受旱。"
            },
            "干旱红色": {
                "icon": "https://upload.wikimedia.org/wikipedia/commons/b/b9/Red_drought_alert_-_China.svg",
                "description": "预计未来一周综合气象干旱指数达到特旱（气象干旱为50年以上一遇），或者某一县（区）有60%以上的农作物受旱。"
            },
            "雷电黄色": {
                "icon": "https://upload.wikimedia.org/wikipedia/commons/c/cf/Yellow_lightening_alert_-_China.svg",
                "description": "6小时内可能发生雷电活动，可能会造成雷电灾害事故。"
            },
            "雷电橙色": {
                "icon": "https://upload.wikimedia.org/wikipedia/commons/5/55/Orange_lightening_alert_-_China.svg",
                "description": "2小时内发生雷电活动的可能性很大，或者已经受雷电活动影响，且可能持续，出现雷电灾害事故的可能性比较大。"
            },
            "雷电红色": {
                "icon": "https://upload.wikimedia.org/wikipedia/commons/e/e9/Red_lightening_alert_-_China.svg",
                "description": "2小时内发生雷电活动的可能性非常大，或者已经有强烈的雷电活动发生，且可能持续，出现雷电灾害事故的可能性非常大。"
            },
            "冰雹橙色": {
                "icon": "https://upload.wikimedia.org/wikipedia/commons/8/8a/Orange_hail_alert_-_China.svg",
                "description": "6小时内可能出现冰雹伴随雷电天气，并可能造成雹灾。"
            },
            "冰雹红色": {
                "icon": "https://upload.wikimedia.org/wikipedia/commons/7/79/Red_hail_alert_-_China.svg",
                "description": "2小时内出现冰雹伴随雷电天气的可能性极大，并可能造成重雹灾。"
            },
            "霜冻蓝色": {
                "icon": "https://upload.wikimedia.org/wikipedia/commons/9/91/Blue_frost_alert_-_China.svg",
                "description": "48小时内地面最低温度将要下降到0℃以下，对农业将产生影响，或者已经降到0℃以下，对农业已经产生影响，并可能持续。"
            },
            "霜冻黄色": {
                "icon": "https://upload.wikimedia.org/wikipedia/commons/f/fe/Yellow_frost_alert_-_China.svg",
                "description": "24小时内地面最低温度将要下降到零下3℃以下，对农业将产生严重影响，或者已经降到零下3℃以下，对农业已经产生严重影响，并可能持续。"
            },
            "霜冻橙色": {
                "icon": "https://upload.wikimedia.org/wikipedia/commons/d/de/Orange_frost_alert_-_China.svg",
                "description": "24小时内地面最低温度将要下降到零下5℃以下，对农业将产生严重影响，或者已经降到零下5℃以下，对农业已经产生严重影响，并将持续。"
            },
            "大雾黄色": {
                "icon": "https://upload.wikimedia.org/wikipedia/commons/5/51/Yellow_heavy_fog_alert_-_China.svg",
                "description": "12小时内可能出现能见度小于500米的浓雾，或者已经出现能见度小于500米、大于等于200米的浓雾且可能持续。"
            },
            "大雾橙色": {
                "icon": "https://upload.wikimedia.org/wikipedia/commons/6/6f/Orange_heavy_fog_alert_-_China.svg",
                "description": "6小时内可能出现能见度小于200米的浓雾，或者已经出现能见度小于200米、大于等于50米的浓雾且可能持续。"
            },
            "大雾红色": {
                "icon": "https://upload.wikimedia.org/wikipedia/commons/9/95/Red_heavy_fog_alert_-_China.svg",
                "description": "2小时内可能出现能见度低于50米的强浓雾，或者已经出现能见度低于50米的强浓雾且可能持续。"
            },
            "霾黄色": {
                "icon": "https://upload.wikimedia.org/wikipedia/commons/1/15/Yellow_haze_alert_-_China.svg",
                "description": "12小时内可能出现能见度小于3000米的霾，或者已经出现能见度小于3000米的霾且可能持续。"
            },
            "霾橙色": {
                "icon": "https://upload.wikimedia.org/wikipedia/commons/e/ef/Orange_haze_alert_-_China.svg",
                "description": "6小时内可能出现能见度小于2000米的霾，或者已经出现能见度小于2000米的霾且可能持续。"
            },
            "道路结冰黄色": {
                "icon": "https://upload.wikimedia.org/wikipedia/commons/9/99/Yellow_road_icing_alert_-_China.svg",
                "description": "当路表温度低于0℃，出现降水，12小时内可能出现对交通有影响的道路结冰。"
            },
            "道路结冰橙色": {
                "icon": "https://upload.wikimedia.org/wikipedia/commons/1/13/Orange_road_icing_alert_-_China.svg",
                "description": "当路表温度低于0℃，出现降水，6小时内可能出现对交通有较大影响的道路结冰。"
            },
            "道路结冰红色": {
                "icon": "https://upload.wikimedia.org/wikipedia/commons/5/5e/Red_road_icing_alert_-_China.svg",
                "description": "当路表温度低于0℃，出现降水，2小时内可能出现或者已经出现对交通有很大影响的道路结冰。"
            }
        }
        if alert_name in alert_data:
            return alert_data[alert_name]
        else:
            return {
                "icon": "https://shiny-push.oss-ap-southeast-1.aliyuncs.com/SHINY_KOTORI_PLACEHOLDER.jpg",
                "description": "暂无描述"
            }

    def main(self):
        result = self.fetch("http://www.nmc.cn/").decode('utf-8')
        soup = BeautifulSoup(result)
        warning_list = soup.select('div.alarm')
        tz = pytz.timezone('Asia/Shanghai')
        if len(warning_list) > 0:
            for item in warning_list:
                warning_desc = item.select('.data-desc')[0]
                warning_title = warning_desc.get_text()[2:]
                warning_url = 'http://www.nmc.cn' + item.select('a')[0].attrs['href']
                if '蓝色' in warning_title or '黄色' in warning_title:
                    alert_name = re.search('发布(.+)预警', warning_title)
                    if alert_name is None:
                        continue
                    alert_name = alert_name.group(1)
                    self.record(3, {
                        "title": "CMA·全国级预警速报",
                        "link": warning_url,
                        "content": warning_title + '(' + datetime.datetime.fromtimestamp(int(time.time()), tz).strftime('%Y-%m-%d') + ')',
                        "cover": self.parse_alert(alert_name)["icon"],
                        "description": self.parse_alert(alert_name)["description"],
                        "alertName": alert_name
                    })
                if '橙色' in warning_title or '红色' in warning_title:
                    alert_name = re.search('发布(.+)预警', warning_title)
                    if alert_name is None:
                        continue
                    alert_name = alert_name.group(1)
                    if '解除' in warning_title:
                        self.record(3, {
                            "title": "CMA·全国级预警速报",
                            "link": warning_url,
                            "content": warning_title + '(' + datetime.datetime.fromtimestamp(int(time.time()), tz).strftime('%Y-%m-%d') + ')',
                            "cover": self.parse_alert(alert_name)["icon"],
                            "description": self.parse_alert(alert_name)["description"],
                            "alertName": alert_name
                        })
                    else:
                        self.record(4, {
                            "title": "CMA·全国级预警速报",
                            "link": warning_url,
                            "content": warning_title + '(' + datetime.datetime.fromtimestamp(int(time.time()), tz).strftime('%Y-%m-%d') + ')',
                            "cover": self.parse_alert(alert_name)["icon"],
                            "description": self.parse_alert(alert_name)["description"],
                            "alertName": alert_name
                        })

    def check(self, timestamp):
        return self.check_expiration(timestamp, 180)
