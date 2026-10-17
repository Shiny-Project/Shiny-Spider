from collections import Counter
from pathlib import Path
import unittest
from unittest.mock import patch

from core import jma
from core.spider import Spider
from core.utils import load_spider
from spiders.weather import jma_ew
from test_jma_ew import feed, report


class SpiderIntegrationTests(unittest.TestCase):
    def setUp(self):
        jma._cache.clear()
        jma_ew._previous_reports.clear()

    def test_scheduler_loaded_spiders_share_downloads_and_submit_expected_publishers(self):
        fixtures = Path(__file__).parent / 'fixtures' / 'jma'
        typhoon_url = 'https://example.test/1_0_VPTW60_010000.xml'
        warning_url = 'https://example.test/2_0_VPWW55_140000.xml'
        files = {
            jma.FEED_URL: feed([(typhoon_url, '1'), (warning_url, '2')]),
            typhoon_url: (fixtures / '10_04_01_170908_VPTW60.xml').read_bytes(),
            warning_url: (fixtures / 'VPWW55_JPTF_170930.xml').read_bytes(),
        }
        with patch.object(Spider, 'fetch', side_effect=files.__getitem__) as fetch, \
                patch('core.database.create_event') as submit:
            load_spider('weather/jma_typhoon').JMATyphoonSpider().main()
            load_spider('weather/jma_ew').JMAEWSpider().main()
            # 调度器再次加载入口，仍然应复用缓存。
            load_spider('weather/jma_ew').JMAEWSpider().main()
        counts = Counter(call[0][0] for call in fetch.call_args_list)
        self.assertEqual(counts, {jma.FEED_URL: 1, typhoon_url: 1, warning_url: 1})
        self.assertEqual([call[0][2] for call in submit.call_args_list], ['JMATyphoon', 'JMAEW', 'JMAEW'])
        first, second = submit.call_args_list[1:]
        self.assertEqual(first[0][0], 4)
        self.assertEqual(first[0][3], second[0][3])
        self.assertEqual(len(first[0][1]['warning']['active']['33']), 35)
        self.assertNotIn('isRelease', first[0][1])

    def test_bodyless_cancellation_keeps_history_between_scheduled_jobs(self):
        issue_url = 'https://example.test/1_0_VPWW55_140000.xml'
        cancel_url = 'https://example.test/2_0_VPWW55_140000.xml'
        files = {
            jma.FEED_URL: feed([(issue_url, '2026-10-17T01:00:00Z')]),
            issue_url: report([('33', '発表', '1410011', None)]),
            cancel_url: report(info_type='取消', date='2026-10-17T01:01:00Z', body=False),
        }
        with patch.object(Spider, 'fetch', side_effect=files.__getitem__), \
                patch('core.database.create_event') as submit:
            load_spider('weather/jma_ew').JMAEWSpider().main()
            jma._cache.pop(jma.FEED_URL)
            files[jma.FEED_URL] = feed([(cancel_url, '2026-10-17T01:01:00Z')])
            load_spider('weather/jma_ew').JMAEWSpider().main()
        self.assertEqual(submit.call_count, 2)
        cancellation = submit.call_args_list[1][0][1]['warning']
        self.assertEqual(cancellation['infoType'], '取消')
        self.assertEqual(cancellation['active'], {})
        self.assertEqual(cancellation['ended'], {'33': ['1410011']})

    def test_submission_levels_follow_status_and_remaining_active_warnings(self):
        active = [('33', '発表', '1410011', None)]
        ended = [('33', '解除', '1410011', '33')]
        partial = [('33', '継続', '1410011', '33'),
                   ('43', '特別警報から危険警報', '1410012', '33')]
        cases = [
            (report(active), 4),
            (report(active, status='訓練'), 3),
            (report(active, status='試験'), 3),
            (report(ended), 3),
            (report([('43', '特別警報から危険警報', '1410011', '33')]), 3),
            (report(partial), 4),
            (report(active, info_type='訂正'), 4),
            (report(ended, info_type='訂正'), 3),
            (report(active, info_type='取消'), 4),
            (report(active, status='訓練', info_type='取消'), 3),
        ]
        generated = [jma_ew.make_event(jma_ew.read_report(data), 'sample') for data, level in cases]
        module = load_spider('weather/jma_ew')
        with patch.object(module, 'events', return_value=iter(generated)), \
                patch('core.database.create_event') as submit:
            module.JMAEWSpider().main()
        self.assertEqual([call[0][0] for call in submit.call_args_list], [level for data, level in cases])


if __name__ == '__main__':
    unittest.main()
