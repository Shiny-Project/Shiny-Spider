"""将 JMA 市町村级警报电文转换为 EW 事件。"""

from collections import OrderedDict, defaultdict
from datetime import datetime
import hashlib
import json
import re
import xml.etree.ElementTree as ET

from core import spider
from core.jma import FEED_URL, fetch_xml


KINDS = {
    '32': '暴风雪特别警报', '33': '大雨特别警报', '35': '暴风特别警报',
    '36': '大雪特别警报', '37': '波浪特别警报', '38': '高潮特别警报',
    '39': '土砂灾害特别警报',
}
# VPWW53 没有 LastKind，用降级后的种类还原被解除的特别警报。
DOWNGRADED_KINDS = {
    '02': '32', '13': '32', '03': '33', '10': '33', '43': '33',
    '05': '35', '15': '35', '06': '36', '12': '36',
    '07': '37', '16': '37', '08': '38', '19': '38', '48': '38',
    '09': '39', '29': '39', '49': '39',
}
_previous_reports = OrderedDict()


def parse_xml(data):
    root = ET.fromstring(data)
    for element in root.iter():
        element.tag = element.tag.rsplit('}', 1)[-1]
    return root


def feed_entries(data):
    groups = defaultdict(list)
    for entry in parse_xml(data).findall('entry'):
        link = entry.find('link')
        if link is None:
            continue
        url = link.get('href', '')
        match = re.search(r'_(VPWW(?:53|54|55|56|57|58|59|60))_', url)
        if match is None:
            continue
        key = (entry.findtext('author/name', ''), entry.findtext('updated', ''))
        groups[key].append((match[1], url))
    selected = []
    for (office, updated), entries in groups.items():
        # VPWW53 和 VPWW54 的警报状态重复，优先取带 LastKind 的 54。
        has_54 = any(code == 'VPWW54' for code, url in entries)
        selected.extend((updated, code, url) for code, url in entries
                        if code != 'VPWW53' or not has_54)
    return sorted(set(selected))


def read_report(data):
    root = parse_xml(data)
    active, ended = defaultdict(set), defaultdict(set)
    names = {}
    changed = False
    for warning in root.findall('Body/Warning'):
        if warning.get('type') != '気象警報・注意報（市町村等）':
            continue
        for item in warning.findall('Item'):
            area = item.findtext('Area/Code')
            if not area:
                continue
            names[area] = item.findtext('Area/Name', area)
            for kind in item.findall('Kind'):
                code = kind.findtext('Code')
                state = kind.findtext('Status', '')
                previous = kind.findtext('LastKind/Code')
                if code in KINDS:
                    (ended if state == '解除' else active)[code].add(area)
                    changed = changed or state != '継続'
                if previous in KINDS and (previous != code or state == '解除'):
                    ended[previous].add(area)
                    changed = True
                elif state.startswith('特別警報から') and code in DOWNGRADED_KINDS:
                    ended[DOWNGRADED_KINDS[code]].add(area)
                    changed = True
    office = root.findtext('Control/PublishingOffice', '')
    status = root.findtext('Control/Status', '通常')
    report_time = root.findtext('Head/ReportDateTime', '')
    info_type = root.findtext('Head/InfoType', '発表')
    return {
        'active': dict(active), 'ended': dict(ended), 'names': names,
        'changed': changed, 'status': status, 'info_type': info_type,
        'office': office, 'report_time': report_time,
        'time': datetime.fromisoformat(root.findtext('Control/DateTime').replace('Z', '+00:00')),
        'key': (office, root.findtext('Control/Title', ''), status),
        'revision': (office, report_time, status, info_type),
    }


def make_event(report, link, previous=None):
    active = report['active']
    ended = {code: set(areas) for code, areas in report['ended'].items()}
    names = report['names']
    info_type = report['info_type']
    if info_type == '取消':
        affected = report
        if not active and not ended and previous is not None:
            affected = previous
            names = previous['names']
        for field in ('active', 'ended'):
            for code, areas in affected[field].items():
                ended.setdefault(code, set()).update(areas)
        active = {}
    elif not report['changed'] and info_type != '訂正':
        # 其他普通警报发生变化、特别警报仅継続时不另行推送。
        return None
    if not active and not ended:
        return None
    warning = {
        'active': {code: sorted(areas) for code, areas in sorted(active.items())},
        'ended': {code: sorted(areas) for code, areas in sorted(ended.items())},
        'status': report['status'], 'infoType': info_type,
    }
    title = '特别警报'
    if info_type in ('訂正', '取消'):
        title += '（' + {'訂正': '订正', '取消': '电文取消'}[info_type] + '）'
    if report['status'] != '通常':
        title = {'訓練': '【训练】', '試験': '【试验】'}[report['status']] + title
    lines = [title]
    for field, label in (('active', '生效'), ('ended', '电文取消涉及区域' if info_type == '取消' else '解除 / 降级')):
        for code, areas in warning[field].items():
            lines.append('{}（{}）：{}'.format(KINDS[code], label, '、'.join(names[area] for area in areas)))
    identity = [report['office'], report['report_time'], warning]
    if info_type in ('訂正', '取消'):
        identity.append(report['time'].isoformat())
    digest = hashlib.sha256(json.dumps(identity, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()
    return {
        'title': title, 'content': '\n'.join(lines), 'link': link,
        'warning': warning, 'hash': 'jma_ew_' + digest,
    }


def events(fetch):
    reports = []
    failures = []
    for updated, code, url in feed_entries(fetch_xml(FEED_URL, fetch)):
        try:
            reports.append((code, url, read_report(fetch_xml(url, fetch))))
        except Exception as error:
            failures.append('{}: {}'.format(url, error))
    # 有时同次发布的不同电文入 feed 相差几秒，再按电文内部的发布时间去重。
    modern = {report['revision'] for code, url, report in reports if code not in ('VPWW53', 'VPWW54')}
    reports.sort(key=lambda item: item[2]['time'])
    emitted = set()
    for code, url, report in reports:
        previous = _previous_reports.get(report['key'])
        if previous is not None and previous['time'] > report['time']:
            previous = None
        if report['info_type'] != '取消' and (previous is not None or report['key'] not in _previous_reports):
            _previous_reports[report['key']] = report
            _previous_reports.move_to_end(report['key'])
            while len(_previous_reports) > 256:
                _previous_reports.popitem(last=False)
        if code in ('VPWW53', 'VPWW54') and report['revision'] in modern:
            continue
        event = make_event(report, url, previous)
        if event is not None and event['hash'] not in emitted:
            emitted.add(event['hash'])
            yield event
    if failures:
        raise RuntimeError('JMA XML 抓取或解析失败：' + '; '.join(failures))


class JMAEWSpider(spider.Spider):
    """JMA 气象特别警报"""
    name = 'JMAEW'

    def main(self):
        for event in events(self.fetch):
            warning = event['warning']
            training = warning['status'] in ('訓練', '試験')
            released = (warning['infoType'] != '取消'
                        and not any(warning['active'].values())
                        and any(warning['ended'].values()))
            self.record(3 if training or released else 4, event)
