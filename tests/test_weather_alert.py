from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from core import config
from core.spider import Spider
from core.utils import load_spider
from spiders.weather import alert


FIXTURES = Path(__file__).parent / 'fixtures'
# 2026-10-23 从 grepalarm_cn.php 截取宁德市、上海市崇明区两条原始记录，
# 以及 webdata/1012303-20261023144800-0102.html 的完整原始详情。
LIST = (FIXTURES / 'weather-alert-list.js').read_bytes()
DETAIL = (FIXTURES / 'weather-alert-detail.js').read_bytes()
FILENAME = '1012303-20261023144800-0102.html'


def script(data):
    return ('var alarminfo=' + json.dumps(data, ensure_ascii=False) + ';').encode('utf-8')


class WeatherAlertTests(unittest.TestCase):
    def run_spider(self, listing=LIST, detail=DETAIL, keywords=()):
        instance = load_spider('weather/alert').AlertSpider({
            'effect': {'temporaryWatchKeywords': list(keywords)}
        })
        instance.fetch = Mock(side_effect=[listing, detail])
        instance.record = Mock()
        instance.main()
        return instance

    def test_official_samples_preserve_event_fields_and_filter_before_loading_details(self):
        instance = self.run_spider(keywords=['宁德', '宁德市', '上海'])
        instance.record.assert_called_once_with(3, {
            'title': '中国·预警速报',
            'content': '福建省宁德市发布台风黄色预警信号',
            'link': alert.CONTENT_URL + FILENAME,
            'alert_data': {
                'description': alert.parse_alarminfo(DETAIL)['ISSUECONTENT'],
                'title': '福建省宁德市发布台风黄色预警信号',
                'send_time': '2026-10-23 14:48:00',
                'identifier': '35090041600000_20261023144800'
            }
        })
        self.assertIn('宁德市气象台', instance.record.call_args.args[1]['alert_data']['description'])
        first, second = instance.fetch.call_args_list
        self.assertRegex(first.args[0], r'^' + alert.DATA_URL.replace('.', r'\.') + r'\?_=[0-9]+$')
        self.assertEqual(second.args, (alert.DETAIL_URL + FILENAME,))
        self.assertEqual(first.kwargs, {'headers': {'Referer': alert.LIST_URL}})
        self.assertEqual(second.kwargs, first.kwargs)

    def test_default_cities_counties_and_districts_keep_the_existing_filter(self):
        listing = alert.parse_alarminfo(LIST)
        original = listing['data'][0]
        titles = ['浙江省杭州市发布大风蓝色预警信号', '上海市发布台风蓝色预警信号',
                  '河南省郑州市发布暴雨黄色预警信号', '北京市发布大风蓝色预警信号',
                  '浙江省杭州市桐庐县发布暴雨黄色预警信号',
                  '浙江省杭州市上城区发布暴雨黄色预警信号', original[6]]
        rows = []
        details = []
        for title in titles:
            row = deepcopy(original)
            row[6] = title
            rows.append(row)
            detail = alert.parse_alarminfo(DETAIL)
            detail['head'] = title
            details.append(script(detail))
        instance = alert.AlertSpider()
        instance.fetch = Mock(side_effect=[script({'data': rows})] + details[:4])
        instance.record = Mock()
        instance.main()
        self.assertEqual([call.args[1]['content'] for call in instance.record.call_args_list], titles[:4])
        self.assertEqual(instance.fetch.call_count, 5)

    def test_only_issued_red_alerts_have_high_priority(self):
        for title, level in [('福建省宁德市发布暴雨红色预警信号', 4),
                             ('福建省宁德市解除暴雨红色预警信号', 3),
                             ('福建省宁德市发布暴雨橙色预警信号', 3)]:
            with self.subTest(title=title):
                listing = alert.parse_alarminfo(LIST)
                listing['data'][0][6] = title
                detail = alert.parse_alarminfo(DETAIL)
                detail['head'] = title
                instance = self.run_spider(script(listing), script(detail), ['宁德'])
                self.assertEqual(instance.record.call_args.args[0], level)

    def test_empty_list_and_no_matching_city_do_not_load_details_or_emit_events(self):
        for listing in (LIST, script({'count': '0', 'data': []})):
            with self.subTest(listing=listing):
                instance = self.run_spider(listing=listing)
                instance.record.assert_not_called()
                self.assertEqual(instance.fetch.call_count, 1)

    def test_script_parser_handles_site_wrappers_and_rejects_broken_responses(self):
        for content in (LIST, b'\xef\xbb\xbf\n' + LIST, DETAIL, DETAIL.rstrip().rstrip(b';')):
            self.assertIsInstance(alert.parse_alarminfo(content), dict)
        for content in (b'<html>403 Forbidden</html>', b'var alarminfo={bad};',
                        b'var alarminfo={}; alert(1);'):
            with self.subTest(content=content), self.assertRaises(ValueError):
                alert.parse_alarminfo(content)

    def test_referer_is_sent_with_existing_user_agent_and_timeout(self):
        with patch('core.spider.request.urlopen') as open_url:
            open_url.return_value.__enter__.return_value.read.return_value = LIST
            self.assertEqual(Spider().fetch(alert.DATA_URL, headers=alert.HEADERS), LIST)
        request = open_url.call_args.args[0]
        self.assertEqual(request.get_header('Referer'), alert.LIST_URL)
        self.assertTrue(request.get_header('User-agent').startswith('Shiny/'))
        self.assertEqual(open_url.call_args.kwargs, {'timeout': config.SPIDER_REQUEST_TIMEOUT})


if __name__ == '__main__':
    unittest.main()
