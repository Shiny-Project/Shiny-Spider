"""解析 JMA VXKO50～89，提交当前电文供中控记录和筛选。"""

from copy import deepcopy
from datetime import datetime
import hashlib
import json
import re
import xml.etree.ElementTree as ET

from core import spider
from core.jma import FEED_URL, fetch_xml


FORECAST_TYPE = '指定河川洪水予報（予報区域）'
KINDS = {'10', '20', '21', '22', '30', '31', '40', '41', '51', '53'}
SPECIAL_KINDS = {'51', '53'}
LABELS = {'10': '泛滥注意报解除', '20': '泛滥注意报', '21': '泛滥注意报',
          '22': '泛滥注意报', '30': '泛滥警报', '31': '泛滥警报',
          '40': '泛滥危险警报', '41': '泛滥危险警报',
          '51': '泛滥特别警报', '53': '泛滥特别警报（泛滥水预报）'}


def parse_xml(data):
    root = ET.fromstring(data)
    for element in root.iter():
        element.tag = element.tag.rsplit('}', 1)[-1]
    return root


def feed_entries(data):
    entries = set()
    for entry in parse_xml(data).findall('entry'):
        for link in entry.findall('link'):
            url = link.get('href', '')
            if re.search(r'_VXKO[5-8]\d(?:_|\.xml$)', url):
                entries.add((entry.findtext('updated', ''), url))
    return sorted(entries)


def timestamp(value):
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.utcoffset() is None:
        raise ValueError('洪水电文时间缺少时区')
    return result


def read_report(data):
    root = parse_xml(data)
    if root.findtext('Control/Title') != '指定河川洪水予報':
        raise ValueError('不是指定河川洪水预报电文')
    status = root.findtext('Control/Status', '通常')
    info_type = root.findtext('Head/InfoType', '発表')
    if status not in ('通常', '訓練', '試験') or info_type not in ('発表', '訂正', '取消'):
        raise ValueError('未知洪水电文状态或发布类型')
    event_id = root.findtext('Head/EventID', '').strip()
    if not re.fullmatch(r'\d{12}', event_id):
        raise ValueError('无效的河川预报区 EventID')
    river, name = None, ''
    for item in root.findall('Head/Headline/Information[@type="' + FORECAST_TYPE + '"]/Item'):
        kind = item.findtext('Kind/Code', '').strip()
        if kind not in KINDS:
            raise ValueError('未知洪水情报种类代码：' + kind)
        for area in item.findall('Areas/Area'):
            code = area.findtext('Code', '').strip()
            if code != event_id:
                raise ValueError('河川预报区代码与 EventID 不一致')
            value = {'code': code, 'kind': kind}
            if river is not None and river != value:
                raise ValueError('同一河川预报区存在冲突状态')
            river = value
            name = area.findtext('Name', code).strip() or code
    if river is None and info_type != '取消':
        raise ValueError('洪水电文缺少河川预报区状态')

    areas, occurred, details = set(), set(), []
    for item in root.findall('Body/Warning[@type="指定河川洪水予報"]/Item'):
        kind = item.findtext('Kind/Code', '').strip()
        if kind in ('1', '2'):
            for city in item.findall('Areas/Area/CityCode'):
                code = (city.text or '').strip()
                if not re.fullmatch(r'\d{7}', code):
                    raise ValueError('无效的洪水预报市町村代码：' + code)
                (areas if kind == '1' else occurred).add(code)
        for prop in item.findall('Kind/Property'):
            if prop.findtext('Type') == '主文':
                text = prop.findtext('Text', '').strip()
                if text and text not in details:
                    details.append(text)
    if river is not None:
        if areas:
            river['areas'] = sorted(areas)
        if occurred:
            if river['kind'] not in SPECIAL_KINDS:
                raise ValueError('非特别警报电文含泛滥发生区域')
            river['occurredAreas'] = sorted(occurred)
    warning = {'status': status, 'infoType': info_type, 'rivers': [river] if river else []}
    notice = root.findtext('Body/Notice', '').strip()
    cancellation = root.findtext('Body/Text', '').strip() if info_type == '取消' else ''
    return {
        'warning': warning, 'name': name, 'event_id': event_id,
        'time': timestamp(root.findtext('Control/DateTime', '')),
        'report_time': timestamp(root.findtext('Head/ReportDateTime', '')).isoformat(),
        'serial': root.findtext('Head/Serial', '').strip(),
        'headline': root.findtext('Head/Headline/Text', '').strip(),
        'details': [text for text in [notice, cancellation] + details if text],
    }


def make_event(report, link):
    warning = deepcopy(report['warning'])
    name = report['name']
    title = name + ' ' + LABELS[warning['rivers'][0]['kind']] if warning['rivers'] else '洪水情报'
    if warning['infoType'] in ('訂正', '取消'):
        title += '（' + {'訂正': '订正', '取消': '电文取消'}[warning['infoType']] + '）'
    if warning['status'] != '通常':
        title = {'訓練': '【训练】', '試験': '【试验】'}[warning['status']] + title
    lines = list(dict.fromkeys([title, report['headline']] + report['details']))
    identity = [report['event_id'], report['time'].isoformat(), report['report_time'],
                report['serial'], name, warning, report['headline'], report['details']]
    digest = hashlib.sha256(json.dumps(identity, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()
    return {
        'title': title, 'content': '\n'.join(text for text in lines if text), 'link': link,
        'hash': 'jma_flood_' + digest,
        'flood_data': {
            'code': report['event_id'], 'name': name, 'time': report['time'].isoformat(),
            'reportTime': report['report_time'], 'serial': report['serial'],
            'warning': warning, 'headline': report['headline'], 'details': report['details'],
        },
    }


def events(fetch):
    reports, failures = [], []
    for updated, url in feed_entries(fetch_xml(FEED_URL, fetch)):
        try:
            reports.append((url, read_report(fetch_xml(url, fetch))))
        except Exception as error:
            failures.append('{}: {}'.format(url, error))
    emitted = set()
    order = {'発表': 0, '訂正': 1, '取消': 2}
    for url, report in sorted(reports, key=lambda item: (item[1]['time'], order[item[1]['warning']['infoType']])):
        event = make_event(report, url)
        if event['hash'] not in emitted:
            emitted.add(event['hash'])
            yield event
    if failures:
        raise RuntimeError('JMA 洪水 XML 抓取或解析失败：' + '; '.join(failures))


class JMAFloodSpider(spider.Spider):
    """JMA 指定河川洪水预报（VXKO50～89）"""
    name = 'JMAFlood'

    def main(self):
        for event in events(self.fetch):
            warning = event['flood_data']['warning']
            routine = warning['status'] != '通常' or not any(
                river['kind'] in SPECIAL_KINDS for river in warning['rivers'])
            self.record(3 if routine else 4, event)
