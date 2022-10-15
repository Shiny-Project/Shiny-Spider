# Common Header
from enum import Enum
from bs4 import BeautifulSoup

from core import spider
from utils.helpers import get_text


class TyphoonStatus(Enum):
    NORMAL = 1  # 台风存续
    MOVE_OUT = 2  # 移出管辖区域
    WEAKEN_TO_TD = 3  # 减弱为热带低压
    DEGENERATION = 4  # 变性为温带气旋
    GALE_WARNING = 5  # 即将生成
    NAMING = 6  # 台风命名


class JMATyphoonSpider(spider.Spider):
    """Spider描述"""
    name = 'JMATyphoon'  # 声明Spider名

    def __init__(self, info={}):
        super(JMATyphoonSpider, self).__init__()  # 仅修改类名，不要修改其他

    def parse_typhoon_info(self, data):
        result = {}
        time = data.DateTime.get_text()
        result['time'] = time
        result['status'] = TyphoonStatus.NORMAL
        body_entries = data.Item.find_all(name='Kind')
        for entry in body_entries:
            type_name = entry.Property.Type.get_text()
            if type_name == '呼称':
                result['name_ja'] = get_text(
                    entry, 'Property.TyphoonNamePart.NameKana')
                result['name_en'] = get_text(
                    entry, 'Property.TyphoonNamePart.Name')
                result['number'] = get_text(
                    entry, 'Property.TyphoonNamePart.Number')
                result['remark'] = get_text(
                    entry, 'Property.TyphoonNamePart.Remark')
                if result['remark'] == '台風消滅（域外へ出る）':
                    result['status'] = TyphoonStatus.MOVE_OUT
                if result['remark'] == '台風消滅（熱帯低気圧化）':
                    result['status'] = TyphoonStatus.WEAKEN_TO_TD
                if result['remark'] == '台風消滅（温帯低気圧化）':
                    result['status'] = TyphoonStatus.DEGENERATION
                if result['remark'] == '台風発生予想':
                    result['status'] = TyphoonStatus.GALE_WARNING
                if result['remark'] == '台風発生':
                    result['status'] = TyphoonStatus.NAMING
            if type_name == '階級':
                result['typhoon_class'] = get_text(
                    entry, 'Property.ClassPart.TyphoonClass')
                result['area_class'] = get_text(
                    entry, 'Property.ClassPart.AreaClass')
                result['intensity_class'] = get_text(
                    entry, 'Property.ClassPart.IntensityClass')
            if type_name == '中心':
                result['coordinate'] = get_text(
                    entry, 'Property.CenterPart.Coordinate')
                result['location'] = get_text(
                    entry, 'Property.CenterPart.Location')
                result['direction'] = get_text(
                    entry, 'Property.CenterPart.Direction')
                node = entry.find(name='Speed', attrs={
                                  "type": "移動速度", "unit": "km/h"})
                if node is not None:
                    result['move_speed'] = node.get_text()
                result['pressure'] = get_text(
                    entry, 'Property.CenterPart.Pressure')
                node = entry.find(name='ProbabilityCircle')
                if node is not None:
                    result['probability_circle'] = {}
                    result['probability_circle']['base_point'] = get_text(
                        entry, 'Property.CenterPart.ProbabilityCircle.BasePoint')
                    node = entry.find(name='Radius', attrs={'unit': 'km'})
                    if node is not None:
                        result['probability_circle']['radius'] = node.get_text()
            if type_name == '風':
                node = entry.find(name='WindSpeed', attrs={
                                  "type": "最大風速", "unit": "m/s"})
                if node is not None:
                    result['near_center_wind_speed'] = node.get_text()

                node = entry.find(name='WindSpeed', attrs={
                                  "type": "最大瞬間風速", "unit": "m/s"})
                if node is not None:
                    result['max_instantaneous_wind_speed'] = node.get_text()

                node = entry.find(name='WarningAreaPart', attrs={
                    "type": '暴風域'
                })

                if node is not None:
                    result['storm_wind_area'] = {}
                    axes = node.find_all(name='Axis')
                    if len(axes) == 1:
                        # 范围为全域时长短边一致且短边省略
                        radius_node = axes[0].find(
                            name='Radius', attrs={'unit': 'km'})
                        if radius_node is not None:
                            result['storm_wind_area']['wide_side'] = {
                                'direction': '全域',
                                'radius': radius_node.get_text()
                            }
                            result['storm_wind_area']['narrow_side'] = {
                                'direction': '全域',
                                'radius': radius_node.get_text()
                            }
                    elif len(axes) == 2:
                        radius_node = axes[0].find(
                            name='Radius', attrs={'unit': 'km'})
                        if radius_node is not None:
                            result['storm_wind_area']['wide_side'] = {
                                'direction': get_text(axes[0], 'Direction'),
                                'radius': radius_node.get_text()
                            }
                        radius_node = axes[1].find(
                            name='Radius', attrs={'unit': 'km'})
                        if radius_node is not None:
                            result['storm_wind_area']['wide_side'] = {
                                'direction': get_text(axes[1], 'Direction'),
                                'radius': radius_node.get_text()
                            }

                node = entry.find(name='WarningAreaPart', attrs={
                    "type": '強風域'
                })

                if node is not None:
                    result['strong_wind_area'] = {}
                    axes = node.find_all(name='Axis')
                    if len(axes) == 1:
                        # 范围为全域时长短边一致且短边省略
                        radius_node = axes[0].find(
                            name='Radius', attrs={'unit': 'km'})
                        if radius_node is not None:
                            result['strong_wind_area']['wide_side'] = {
                                'direction': '全域',
                                'radius': radius_node.get_text()
                            }
                            result['strong_wind_area']['narrow_side'] = {
                                'direction': '全域',
                                'radius': radius_node.get_text()
                            }
                    elif len(axes) == 2:
                        radius_node = axes[0].find(
                            name='Radius', attrs={'unit': 'km'})
                        if radius_node is not None:
                            result['strong_wind_area']['wide_side'] = {
                                'direction': get_text(axes[0], 'Direction'),
                                'radius': radius_node.get_text()
                            }
                        radius_node = axes[1].find(
                            name='Radius', attrs={'unit': 'km'})
                        if radius_node is not None:
                            result['strong_wind_area']['narrow_side'] = {
                                'direction': get_text(axes[1], 'Direction'),
                                'radius': radius_node.get_text()
                            }

        return result

    def generate_content(self, data):
        if data['current']['remark'] == '台風消滅（域外へ出る）':
            return "台风 {} 移出管辖范围，这是关于 {} 的最后一次报告".format(data['current']['name_en'], data['current']['name_en'])
        if data['current']['remark'] == '台風消滅（熱帯低気圧化）':
            return "台风 {} 减弱为热带低压，当前位于 {}，这是关于 {} 的最后一次报告".format(data['current']['name_en'], data['current']['location'], data['current']['name_en'])
        if data['current']['remark'] == '台風消滅（温帯低気圧化）':
            return "台风 {} 变性为温带气旋，当前位于 {}，这是关于 {} 的最后一次报告".format(data['current']['name_en'], data['current']['location'], data['current']['name_en'])

        current_location_text = ''

        if data['current']['remark'] == '台風発生予想':
            current_location_text = '一热带低压即将加强为台风，当前位于 {}，'.format(
                data['current']['name_en'], data['current']['location'])
        elif data['current']['remark'] == '台風発生':
            current_location_text = '台风 {} 现已被命名，当前位于 {}，'.format(
                data['current']['name_en'], data['current']['location'])
        else:
            current_location_text = '台风 {} 当前位于 {}，'.format(
                data['current']['name_en'], data['current']['location'])

        current_status_text = '中心气压 {} 百帕，近中心最大风力 {} 米每秒（十分钟平均），'.format(
            data['current']['pressure'], data['current']['near_center_wind_speed'])

        current_movement_text = ''

        if data['current']['direction'] == '' or data['current']['move_speed'] == '':
            current_movement_text = '在原地停滞少动。'
        else:
            current_movement_text = '正向 {} 方向以 {} 千米每小时速度移动。'.format(
                data['current']['direction'], data['current']['move_speed'])

        return '{}{}{}'.format(current_location_text, current_status_text, current_movement_text)

    def main(self):
        """在这里执行你的主抓取逻辑"""
        url = 'https://www.data.jma.go.jp/developer/xml/feed/extra.xml'
        response = self.fetch(url)
        html = BeautifulSoup(response, "xml", from_encoding="utf-8")
        entries = html.find_all(name="entry")
        typhoon_entry_links = []

        for entry in entries:
            if 'VPTW60' in entry.id.get_text():
                typhoon_entry_links.append(entry.link.attrs['href'])
        for link in typhoon_entry_links:
            result = {}
            result['estimations'] = []
            typhoon_data = BeautifulSoup(self.fetch(
                link), "xml", from_encoding="utf-8")
            info_item = typhoon_data.find_all(name="MeteorologicalInfo")
            for item in info_item:
                item_type = item.DateTime.attrs['type']
                if item_type == '実況':
                    result["current"] = self.parse_typhoon_info(item)
                else:
                    result['estimations'].append(
                        self.parse_typhoon_info(item)
                    )

            self.record(3, {
                "title": "台风消息",
                "link": link,
                "content": self.generate_content(result),
                "cover": "",
                "typhoon_data": result,
            })
            break  # use first one


if __name__ == '__main__':
    pass
