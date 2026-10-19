"""将 JMA VFVO56 喷火速报转换为文本事件。"""

from datetime import datetime
import hashlib
import json
import re
import xml.etree.ElementTree as ET

from core import spider
from core.jma import EQVOL_FEED_URL, fetch_xml


KINDS = {'52': '发生喷发', '62': '疑似喷发'}


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
            if re.search(r'_VFVO56(?:_|\.xml$)', url):
                entries.add((entry.findtext('updated', ''), url))
    return sorted(entries)


def timestamp(value):
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.utcoffset() is None:
        raise ValueError('喷火速报时间缺少时区')
    return result


def read_report(data):
    root = parse_xml(data)
    if root.findtext('Control/Title') != '噴火速報':
        raise ValueError('不是 VFVO56 喷火速报电文')
    status = root.findtext('Control/Status', '通常')
    info_type = root.findtext('Head/InfoType', '発表')
    if status not in ('通常', '訓練', '試験') or info_type not in ('発表', '訂正', '取消'):
        raise ValueError('未知的喷火速报状态或发布类型')
    event_id = root.findtext('Head/EventID', '').strip()
    match = re.fullmatch(r'\d{14}_(\d{3})', event_id)
    if match is None:
        raise ValueError('无效的喷火速报 EventID')
    code = match[1]
    eruption = {'eventId': event_id, 'status': status, 'infoType': info_type, 'areas': []}
    items = root.findall('Body/VolcanoInfo[@type="噴火速報"]/Item')
    if not items:
        items = root.findall('Head/Headline/Information[@type="噴火速報"]/Item')
    if len(items) > 1:
        raise ValueError('喷火速报包含多个目标火山状态')
    name = ''
    if items:
        area = items[0].findall('Areas/Area')
        if len(area) != 1 or area[0].findtext('Code', '').strip() != code:
            raise ValueError('喷火速报目标火山与 EventID 不一致')
        name = area[0].findtext('Name', '').strip()
    if not name:
        title = root.findtext('Head/Title', '').strip()
        match = re.fullmatch(r'火山名\s+(.+?)\s+噴火速報', title)
        name = match[1] if match else '火山 ' + code
    eruption['volcano'] = {'code': code, 'name': name}
    cancelled = info_type == '取消'
    if not cancelled:
        if not items or items[0].findtext('Kind/Code', '').strip() not in KINDS:
            raise ValueError('喷火速报缺少有效的喷发现象代码')
        eruption['kind'] = items[0].findtext('Kind/Code').strip()
        observed = items[0].find('EventTime/EventDateTime')
        if observed is None or not (observed.text or '').strip():
            observed = items[0].find('EventTime/EventDateTimeUTC')
        event_time = (observed.text or '').strip() if observed is not None else ''
        if event_time:
            precision = observed.get('significant', 'yyyy-mm-ddThh:mm')
            dubious = observed.get('dubious', '')
        else:
            event_time = root.findtext('Head/TargetDateTime', '').strip()
            precision = 'yyyy-mm-ddThh:mm'
            dubious = root.findtext('Head/TargetDTDubious', '').strip()
        if event_time:
            timestamp(event_time)
            eruption.update(time=event_time, timePrecision=precision, timeDubious=dubious)
        areas = {}
        for item in root.findall('Body/VolcanoInfo[@type="噴火速報（対象市町村等）"]/Item'):
            if item.findtext('Kind/Code', '').strip() != eruption['kind']:
                raise ValueError('喷火速报市町村与目标火山的现象代码不一致')
            for area in item.findall('Areas/Area'):
                area_code = area.findtext('Code', '').strip()
                if not re.fullmatch(r'\d{7}', area_code):
                    raise ValueError('无效的喷火速报市町村代码：' + area_code)
                areas[area_code] = {'code': area_code, 'name': area.findtext('Name', area_code).strip()}
        eruption['areas'] = [areas[key] for key in sorted(areas)]
    if cancelled:
        details = [root.findtext('Body/Text', '').strip() or root.findtext('Head/Headline/Text', '').strip()]
    else:
        details = [root.findtext('Body/VolcanoInfoContent/' + field, '').strip()
                   for field in ('VolcanoActivity', 'VolcanoPrevention', 'Appendix', 'Text')]
        if not any(details):
            details = [root.findtext('Body/VolcanoInfoContent/VolcanoHeadline', '').strip()
                       or root.findtext('Head/Headline/Text', '').strip()]
    notice = root.findtext('Body/Notice', '').strip()
    return {
        'eruption': eruption, 'time': timestamp(root.findtext('Control/DateTime', '')),
        'report_time': timestamp(root.findtext('Head/ReportDateTime', '')),
        'details': [text for text in [notice] + details if text],
    }


def make_event(report, link):
    eruption = report['eruption']
    info_type = eruption['infoType']
    title = eruption['volcano']['name'] + ' 喷火速报'
    if info_type != '取消':
        title += ' · ' + KINDS[eruption['kind']]
    if info_type in ('訂正', '取消'):
        title += '（' + {'訂正': '订正', '取消': '电文取消'}[info_type] + '）'
    if eruption['status'] != '通常':
        title = {'訓練': '【训练】', '試験': '【试验】'}[eruption['status']] + title
    lines = [title]
    if eruption['areas']:
        lines.append('涉及市町村：' + '、'.join(area['name'] for area in eruption['areas']))
    lines.extend(report['details'])
    identity = [report['time'].isoformat(), report['report_time'].isoformat(), eruption, report['details']]
    digest = hashlib.sha256(json.dumps(identity, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()
    return {'title': title, 'content': '\n'.join(lines), 'link': link,
            'eruption': eruption, 'hash': 'jma_eruption_' + digest}


def events(fetch):
    reports, failures = [], []
    for updated, url in feed_entries(fetch_xml(EQVOL_FEED_URL, fetch)):
        try:
            reports.append((url, read_report(fetch_xml(url, fetch))))
        except Exception as error:
            failures.append('{}: {}'.format(url, error))
    emitted = set()
    for url, report in sorted(reports, key=lambda item: item[1]['time']):
        event = make_event(report, url)
        if event['hash'] not in emitted:
            emitted.add(event['hash'])
            yield event
    if failures:
        raise RuntimeError('JMA 喷火速报 XML 抓取或解析失败：' + '; '.join(failures))


class JMAEruptionSpider(spider.Spider):
    """JMA 喷火速报（VFVO56）"""
    name = 'JMAEruption'

    def main(self):
        for event in events(self.fetch):
            self.record(4 if event['eruption']['status'] == '通常' else 3, event)
