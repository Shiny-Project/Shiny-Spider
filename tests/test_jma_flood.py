from copy import deepcopy
import hashlib
import importlib
import json
from pathlib import Path
import unittest
from unittest.mock import Mock, patch
import xml.etree.ElementTree as ET

from core import jma
from core.spider import Spider
from core.utils import load_spider
from spiders.weather import jma_flood
from test_jma_ew import feed


FIXTURES = Path(__file__).parent / 'fixtures'
SOURCES = json.loads((FIXTURES / 'jma-flood-sources.json').read_text(encoding='utf-8'))['samples']
URL = 'https://example.test/1_0_VXKO50_010000.xml'


def report(kind='51', status='通常', info_type='発表', time='2026-10-22T01:00:00Z',
           report_time=None, serial='1', body=True, headline=True):
    root = jma_flood.parse_xml((FIXTURES / 'jma' / SOURCES[6]['file']).read_bytes())
    for path, value in [('Control/DateTime', time), ('Control/Status', status),
                        ('Head/InfoType', info_type), ('Head/ReportDateTime', report_time or time),
                        ('Head/Serial', serial)]:
        root.find(path).text = value
    for element in root.findall('Head/Headline/Information/Item/Kind/Code'):
        element.text = kind
    if not body:
        root.remove(root.find('Body'))
    if not headline:
        root.find('Head').remove(root.find('Head/Headline'))
    return root


def event(root):
    return jma_flood.make_event(jma_flood.read_report(ET.tostring(root, encoding='utf-8')), URL)


class FloodTests(unittest.TestCase):
    def setUp(self):
        jma._cache.clear()

    def test_all_official_reports_are_submitted_with_self_contained_time_series_data(self):
        events = []
        for sample in SOURCES:
            data = (FIXTURES / 'jma' / sample['file']).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), sample['sha256'])
            parsed = jma_flood.read_report(data)
            result = jma_flood.make_event(parsed, URL)
            source = result['flood_data']
            self.assertEqual(source['warning']['rivers'][0]['kind'], sample['kind'])
            self.assertEqual(source['code'], parsed['event_id'])
            self.assertEqual(source['time'], parsed['time'].isoformat())
            self.assertEqual(source['reportTime'], parsed['report_time'])
            self.assertEqual(source['serial'], parsed['serial'])
            self.assertNotIn('warning', result)
            events.append(result)
        self.assertEqual(len(events), 14)
        self.assertNotIn('occurredAreas', events[6]['flood_data']['warning']['rivers'][0])
        self.assertEqual(events[7]['flood_data']['warning']['rivers'][0]['occurredAreas'], ['0636700'])
        self.assertNotIn('areas', events[7]['flood_data']['warning']['rivers'][0])
        self.assertEqual(len(events[9]['flood_data']['warning']['rivers'][0]['occurredAreas']), 33)
        self.assertIn('氾濫が発生', events[7]['content'])

    def test_all_lower_kinds_are_submitted_even_after_a_fresh_module_load(self):
        for kind in sorted(jma_flood.KINDS):
            importlib.reload(jma_flood)
            data = ET.tostring(report(kind=kind))
            files = {jma.FEED_URL: feed([(URL, '1')]), URL: data}
            jma._cache.clear()
            with patch.object(Spider, 'fetch', side_effect=files.__getitem__), patch('core.database.create_event') as submit:
                load_spider('weather/jma_flood').JMAFloodSpider().main()
            self.assertEqual(submit.call_count, 1)
            source = submit.call_args.args[1]['flood_data']
            self.assertEqual(source['warning']['rivers'][0]['kind'], kind)
            self.assertNotIn('特别警报降级', submit.call_args.args[1]['title'])

    def test_bodyless_cancellation_is_submitted_without_borrowing_a_previous_warning(self):
        root = report(info_type='取消', body=False, headline=False)
        first = event(root)
        self.assertEqual(first['flood_data']['warning']['rivers'], [])
        self.assertEqual(first['flood_data']['code'], '820211000103')
        self.assertIn('电文取消', first['title'])
        event(report())
        self.assertEqual(event(root), first)
        importlib.reload(jma_flood)
        self.assertEqual(event(root), first)

    def test_feed_covers_all_40_vxko_products_and_ignores_other_flood_products(self):
        urls = [URL.replace('VXKO50', 'VXKO' + str(code)) for code in range(50, 90)]
        unrelated = [URL.replace('VXKO50', code) for code in ('VXKO49', 'VXKO90', 'VXSU50', 'VPWW55', 'VFVO50')]
        entries = jma_flood.feed_entries(feed([(url, '1') for url in urls + unrelated + urls]))
        self.assertEqual([url for updated, url in entries], sorted(urls))

    def test_hash_deduplicates_links_and_city_order_but_preserves_current_content_and_revisions(self):
        root = report()
        parsed = jma_flood.read_report(ET.tostring(root))
        original = jma_flood.make_event(parsed, URL)
        self.assertEqual(original['hash'], jma_flood.make_event(parsed, 'another-url')['hash'])
        for areas in root.findall('Body/Warning/Item/Areas'):
            areas[:] = reversed(list(areas))
        self.assertEqual(original['hash'], event(root)['hash'])
        root.find('Head/Headline/Text').text += '更新'
        self.assertNotEqual(original['hash'], event(root)['hash'])
        self.assertNotEqual(original['hash'], event(report(info_type='訂正'))['hash'])
        other_url = URL.replace('/1_', '/2_')
        files = {jma.FEED_URL: feed([(URL, '1'), (URL, '1'), (other_url, '2')]),
                 URL: ET.tostring(report()), other_url: ET.tostring(report())}
        fetch = Mock(side_effect=files.__getitem__)
        self.assertEqual(len(list(jma_flood.events(fetch))), 1)
        self.assertEqual(fetch.call_count, 3)

    def test_invalid_codes_metadata_and_conflicting_river_states_fail(self):
        for path, value in [('Control/Title', '噴火警報・予報'), ('Head/EventID', '8202110001'),
                            ('Control/Status', 'normal'), ('Head/InfoType', '解除'),
                            ('Control/DateTime', '2026-10-22T01:00:00'),
                            ('Head/Headline/Information/Item/Areas/Area/Code', '820211000104'),
                            ('Head/Headline/Information/Item/Kind/Code', '50'),
                            ('Body/Warning/Item/Areas/Area/CityCode', '123')]:
            root = report()
            node = root.find(path)
            self.assertIsNotNone(node, path)
            node.text = value
            with self.assertRaises(ValueError, msg=path):
                event(root)
        root = report()
        section = root.find('Head/Headline/Information')
        section.append(deepcopy(section.find('Item')))
        section[-1].find('Kind/Code').text = '53'
        with self.assertRaisesRegex(ValueError, '冲突'):
            event(root)

    def test_priority_and_training_markers_only_depend_on_the_current_telegram(self):
        for kind in ('51', '53', '40', '22', '10'):
            for status in ('通常', '訓練', '試験'):
                result = event(report(kind=kind, status=status))
                expected = 4 if status == '通常' and kind in ('51', '53') else 3
                with patch.object(jma_flood, 'events', return_value=iter([result])), patch('core.database.create_event') as submit:
                    jma_flood.JMAFloodSpider().main()
                self.assertEqual(submit.call_args.args[0], expected)
                self.assertEqual(result['title'].startswith('【'), status != '通常')

    def test_valid_reports_survive_another_failed_download(self):
        bad = URL.replace('/1_', '/2_')
        files = {jma.FEED_URL: feed([(bad, '1'), (URL, '2')]), URL: ET.tostring(report())}
        iterator = jma_flood.events(files.__getitem__)
        self.assertEqual(next(iterator)['link'], URL)
        with self.assertRaisesRegex(RuntimeError, bad):
            next(iterator)


if __name__ == '__main__':
    unittest.main()
