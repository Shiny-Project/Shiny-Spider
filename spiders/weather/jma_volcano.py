"""将 JMA VFVO50 喷火警报、预报电文转换为火山事件。"""

from collections import OrderedDict
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
import re
import xml.etree.ElementTree as ET

from core import spider
from core.jma import EQVOL_FEED_URL, fetch_xml


VOLCANO_TYPE = '噴火警報・予報（対象火山）'
AREA_TYPE = '噴火警報・予報（対象市町村等）'
RESPONSE_TYPE = '噴火警報・予報（対象市町村の防災対応等）'
KINDS = {
    '11': '等级 1 · 留意活火山', '12': '等级 2 · 火口周边管制',
    '13': '等级 3 · 限制进山', '14': '等级 4 · 老年人等避难', '15': '等级 5 · 避难',
    '21': '留意活火山', '22': '火口周边危险', '23': '进山危险',
    '24': '山麓严格警戒', '25': '居住区严格警戒',
    '35': '留意海底活火山', '36': '周边海域警戒',
}
FORECAST_KINDS = {'11', '21', '35'}
SPECIAL_KINDS = {'14', '15', '24', '25'}
CONDITIONS = {'発表', '引上げ', '切替', '継続', '引下げ', '解除'}
SECTION_KINDS = {
    VOLCANO_TYPE: set(KINDS),
    AREA_TYPE: {'01', '02', '03', '04', '05'},
    RESPONSE_TYPE: {str(code) for code in range(41, 50)},
}
_previous_reports = OrderedDict()


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
            if re.search(r'_VFVO50(?:_|\.xml$)', url):
                entries.add((entry.findtext('updated', ''), url))
    return sorted(entries)


def read_report(data):
    root = parse_xml(data)
    if root.findtext('Control/Title') != '噴火警報・予報':
        raise ValueError('不是 VFVO50 喷火警报、预报电文')
    status = root.findtext('Control/Status', '通常')
    info_type = root.findtext('Head/InfoType', '発表')
    if status not in ('通常', '訓練', '試験') or info_type not in ('発表', '訂正', '取消'):
        raise ValueError('未知的火山电文状态或发布类型')
    event_id = root.findtext('Head/EventID', '').strip()
    if not re.fullmatch(r'\d{3}', event_id):
        raise ValueError('缺少有效的火山 EventID')
    warning = {'status': status, 'infoType': info_type, 'areas': [], 'responses': []}
    name = ''
    # 取消电文可以省略 Body；若头部仍有结构化状态，直接使用它。
    sections = root.findall('Body/VolcanoInfo')
    if not sections:
        sections = root.findall('Head/Headline/Information')
    for section in sections:
        section_type = section.get('type')
        if section_type not in SECTION_KINDS:
            continue
        for item in section.findall('Item'):
            kind = item.findtext('Kind/Code', '').strip()
            if kind not in SECTION_KINDS[section_type]:
                raise ValueError('未知火山种类代码：' + kind)
            for area in item.findall('Areas/Area'):
                code = area.findtext('Code', '').strip()
                if section_type == VOLCANO_TYPE:
                    if code != event_id:
                        raise ValueError('目标火山代码与 EventID 不一致')
                    volcano = {'code': code, 'kind': kind}
                    position = area.findtext('Coordinate', '').strip()
                    if position:
                        volcano['coordinate'] = position
                    if 'volcano' in warning and warning['volcano'] != volcano:
                        raise ValueError('一份电文包含冲突的目标火山状态')
                    warning['volcano'] = volcano
                    name = area.findtext('Name', code).strip() or code
                    continue
                if not re.fullmatch(r'\d{7}', code):
                    raise ValueError('无效的火山市町村代码：' + code)
                value = {'code': code, 'kind': kind}
                field = 'areas' if section_type == AREA_TYPE else 'responses'
                condition = item.findtext('Kind/Condition', '').strip()
                if field == 'responses' and condition:
                    if condition not in CONDITIONS:
                        raise ValueError('未知市町村防灾应对状态：' + condition)
                    value['condition'] = condition
                warning[field].append(value)
    for field in ('areas', 'responses'):
        unique = {}
        for value in warning[field]:
            code = value['code']
            if code in unique and unique[code] != value:
                raise ValueError('同一市町村存在冲突状态：' + code)
            unique[code] = value
        warning[field] = [unique[code] for code in sorted(unique)]
    if 'volcano' not in warning and info_type != '取消':
        raise ValueError('火山电文缺少当前目标火山状态')
    return {
        'warning': warning, 'name': name, 'event_id': event_id,
        'time': datetime.fromisoformat(root.findtext('Control/DateTime', '').replace('Z', '+00:00')),
        'report_time': root.findtext('Head/ReportDateTime', ''),
        'headline': root.findtext('Body/VolcanoInfoContent/VolcanoHeadline', '').strip()
                    or root.findtext('Head/Headline/Text', '').strip(),
        'prevention': root.findtext('Body/VolcanoInfoContent/VolcanoPrevention', '').strip(),
        'key': (event_id, status),
    }


def make_event(report, link, previous=None):
    warning = deepcopy(report['warning'])
    name = report['name']
    if 'volcano' not in warning:
        if previous is None:
            raise ValueError('取消电文缺少目标火山状态，且没有可用的先前电文：' + report['event_id'])
        warning = deepcopy(previous['warning'])
        warning.update(status=report['warning']['status'], infoType='取消')
        name = previous['name']
    kind = warning['volcano']['kind']
    cancelled = warning['infoType'] == '取消'
    if kind in FORECAST_KINDS:
        title = '喷火预报'
        if not cancelled and any(area['kind'] == '04' for area in warning['areas']):
            title += ' · 警报解除'
    else:
        title = '喷火特别警报' if kind in SPECIAL_KINDS else '喷火警报'
    title = name + ' ' + title
    if warning['infoType'] in ('訂正', '取消'):
        title += '（' + {'訂正': '订正', '取消': '电文取消'}[warning['infoType']] + '）'
    if warning['status'] != '通常':
        title = {'訓練': '【训练】', '試験': '【试验】'}[warning['status']] + title
    issued = report['time'].astimezone(timezone(timedelta(hours=9))).strftime('%Y/%m/%d %H:%M')
    lines = [title, ('原电文状态：' if cancelled else '') + KINDS[kind],
             '气象厅 {} 发布（日本时间）'.format(issued)]
    lines.extend(text for text in (report['headline'], report['prevention']) if text)
    identity = [report['event_id'], report['time'].isoformat(), report['report_time'],
                warning, report['headline'], report['prevention']]
    digest = hashlib.sha256(json.dumps(identity, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()
    return {
        'title': title, 'content': '\n'.join(lines), 'link': link,
        'warning': warning, 'hash': 'jma_volcano_' + digest,
    }


def events(fetch):
    reports, failures = [], []
    for updated, url in feed_entries(fetch_xml(EQVOL_FEED_URL, fetch)):
        try:
            reports.append((url, read_report(fetch_xml(url, fetch))))
        except Exception as error:
            failures.append('{}: {}'.format(url, error))
    emitted = set()
    for url, report in sorted(reports, key=lambda item: item[1]['time']):
        previous = _previous_reports.get(report['key'])
        if previous is not None and previous['time'] > report['time']:
            previous = None
        try:
            event = make_event(report, url, previous)
        except ValueError as error:
            failures.append('{}: {}'.format(url, error))
            continue
        if report['warning']['infoType'] != '取消' and (
                report['key'] not in _previous_reports or previous is not None):
            _previous_reports[report['key']] = report
            _previous_reports.move_to_end(report['key'])
            while len(_previous_reports) > 256:
                _previous_reports.popitem(last=False)
        if event['hash'] not in emitted:
            emitted.add(event['hash'])
            yield event
    if failures:
        raise RuntimeError('JMA 火山 XML 抓取或解析失败：' + '; '.join(failures))


class JMAVolcanoSpider(spider.Spider):
    """JMA 喷火警报与预报（VFVO50）"""
    name = 'JMAVolcano'

    def main(self):
        for event in events(self.fetch):
            warning = event['warning']
            routine = warning['status'] != '通常' or warning['volcano']['kind'] in FORECAST_KINDS
            self.record(3 if routine else 4, event)
