from copy import deepcopy
from pathlib import Path
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from core import jma
from core.spider import Spider
from core.utils import load_spider
from spiders.weather import jma_volcano
from test_jma_ew import feed


FIXTURES = Path(__file__).parent / 'fixtures' / 'jma'
# Unmodified JMA samples: https://xml.kishou.go.jp/jmaxml_20260917_Samples.zip.
SAMPLES = ['45_01_01_200522_VFVO50.xml', '45_02_01_200522_VFVO50.xml',
           '45_03_01_200731_VFVO50.xml']
ISSUE_URL = 'https://example.test/1_0_VFVO50_010000.xml'
CANCEL_URL = 'https://example.test/2_0_VFVO50_010000.xml'


def report(index=0, status='通常', info_type='発表', date=None, body=True, headline=True):
    root = jma_volcano.parse_xml((FIXTURES / SAMPLES[index]).read_bytes())
    root.find('Control/Status').text = status
    root.find('Head/InfoType').text = info_type
    if date:
        root.find('Control/DateTime').text = date
    if not body:
        root.remove(root.find('Body'))
    if not headline:
        root.find('Head').remove(root.find('Head/Headline'))
    return root


def xml(root):
    return ET.tostring(root, encoding='utf-8')


class VolcanoTests(unittest.TestCase):
    def setUp(self):
        jma._cache.clear()
        jma_volcano._previous_reports.clear()

    def test_official_reports_keep_all_three_types_of_current_state_separate(self):
        results = [jma_volcano.make_event(jma_volcano.read_report(
            (FIXTURES / name).read_bytes()), name) for name in SAMPLES]
        warnings = [result['warning'] for result in results]
        self.assertEqual([item['volcano']['kind'] for item in warnings], ['13', '15', '11'])
        self.assertEqual([len(item['areas']) for item in warnings], [4, 1, 2])
        self.assertEqual([len(item['responses']) for item in warnings], [4, 1, 3])
        self.assertEqual(warnings[0]['volcano'], {
            'code': '306', 'kind': '13', 'coordinate': '+3624.38+13831.38+2568/'})
        self.assertEqual(warnings[0]['areas'][0], {'code': '1042500', 'kind': '02'})
        self.assertEqual(warnings[1]['responses'], [{'code': '1438200', 'kind': '41', 'condition': '発表'}])
        self.assertEqual(warnings[2]['responses'], [
            {'code': '1042100', 'kind': '45', 'condition': '継続'},
            {'code': '1042500', 'kind': '45', 'condition': '解除'},
            {'code': '1042600', 'kind': '45', 'condition': '解除'},
        ])
        self.assertIn('特别警报', results[1]['title'])
        self.assertIn('警报解除', results[2]['title'])
        self.assertIn('2020/05/22 13:03', results[0]['content'])
        self.assertIn('山頂火口から概ね４ｋｍ', results[0]['content'])

    def test_feed_selects_only_vfvo50_and_deduplicates_links(self):
        data = feed([(ISSUE_URL, '2'), (ISSUE_URL, '2'),
                     (CANCEL_URL, '1'), ('https://example.test/1_0_VFVO51_010000.xml', '1'),
                     ('https://example.test/1_0_VFVO60_010000.xml', '1'),
                     ('https://example.test/1_0_VXSE53_010000.xml', '1')])
        self.assertEqual(jma_volcano.feed_entries(data), [('1', CANCEL_URL), ('2', ISSUE_URL)])

    def test_absent_coordinate_is_omitted_for_map_default_positioning(self):
        root = report()
        area = root.find('Body/VolcanoInfo/Item/Areas/Area')
        area.remove(area.find('Coordinate'))
        result = jma_volcano.make_event(jma_volcano.read_report(xml(root)), ISSUE_URL)
        self.assertEqual(result['warning']['volcano'], {'code': '306', 'kind': '13'})

    def test_bodyless_cancellation_can_use_structured_headline(self):
        result = jma_volcano.make_event(jma_volcano.read_report(xml(report(
            info_type='取消', body=False))), CANCEL_URL)
        self.assertEqual(result['warning']['volcano'], {'code': '306', 'kind': '13'})
        self.assertEqual(len(result['warning']['areas']), 4)
        self.assertIn('电文取消', result['title'])
        self.assertIn('原电文状态', result['content'])
        self.assertNotIn('警报解除', result['title'])

    def test_cancellation_keeps_prior_geometry_across_scheduler_polls(self):
        files = {
            jma.EQVOL_FEED_URL: feed([(ISSUE_URL, '1')]),
            ISSUE_URL: xml(report()),
            CANCEL_URL: xml(report(info_type='取消', date='2020-05-22T04:04:00Z', body=False, headline=False)),
        }
        with patch.object(Spider, 'fetch', side_effect=files.__getitem__) as fetch, \
                patch('core.database.create_event') as submit:
            load_spider('weather/jma_volcano').JMAVolcanoSpider().main()
            jma._cache.pop(jma.EQVOL_FEED_URL)
            files[jma.EQVOL_FEED_URL] = feed([(CANCEL_URL, '2')])
            load_spider('weather/jma_volcano').JMAVolcanoSpider().main()
            load_spider('weather/jma_volcano').JMAVolcanoSpider().main()
        self.assertEqual(fetch.call_count, 4)
        self.assertEqual(submit.call_count, 3)
        issued, cancelled, repeated = [call.args for call in submit.call_args_list]
        self.assertEqual(issued[2], 'JMAVolcano')
        self.assertEqual(cancelled[1]['warning']['infoType'], '取消')
        self.assertEqual(cancelled[1]['warning']['volcano'], issued[1]['warning']['volcano'])
        self.assertEqual(cancelled[1]['warning']['areas'], issued[1]['warning']['areas'])
        self.assertEqual(cancelled[3], repeated[3])
        self.assertNotEqual(issued[3], cancelled[3])

    def test_reports_are_processed_by_control_time_even_when_feed_order_differs(self):
        files = {
            jma.EQVOL_FEED_URL: feed([(CANCEL_URL, '1'), (ISSUE_URL, '2')]),
            ISSUE_URL: xml(report()),
            CANCEL_URL: xml(report(info_type='取消', date='2020-05-22T04:04:00Z', body=False, headline=False)),
        }
        results = list(jma_volcano.events(files.__getitem__))
        self.assertEqual([item['warning']['infoType'] for item in results], ['発表', '取消'])

    def test_unresolved_cancellation_fails_without_borrowing_training_or_future_state(self):
        cancellation = jma_volcano.read_report(xml(report(info_type='取消', body=False, headline=False)))
        with self.assertRaisesRegex(ValueError, '没有可用的先前电文'):
            jma_volcano.make_event(cancellation, CANCEL_URL)
        for status, date in [('訓練', '2020-05-22T04:00:00Z'), ('通常', '2020-05-22T04:05:00Z')]:
            jma._cache.clear()
            prior = jma_volcano.read_report(xml(report(status=status, date=date)))
            jma_volcano._previous_reports.clear()
            jma_volcano._previous_reports[prior['key']] = prior
            files = {jma.EQVOL_FEED_URL: feed([(CANCEL_URL, '1')]),
                     CANCEL_URL: xml(report(info_type='取消', body=False, headline=False))}
            with self.assertRaisesRegex(RuntimeError, CANCEL_URL):
                list(jma_volcano.events(files.__getitem__))

    def test_hash_is_stable_across_urls_and_item_order_but_preserves_revisions(self):
        base = jma_volcano.read_report(xml(report()))
        original = jma_volcano.make_event(base, ISSUE_URL)
        self.assertEqual(original['hash'], jma_volcano.make_event(base, CANCEL_URL)['hash'])
        reordered = report()
        section = reordered.find('Body/VolcanoInfo[@type="' + jma_volcano.RESPONSE_TYPE + '"]/Item/Areas')
        section[:] = reversed(list(section))
        self.assertEqual(original['hash'], jma_volcano.make_event(
            jma_volcano.read_report(xml(reordered)), ISSUE_URL)['hash'])
        corrected = jma_volcano.make_event(jma_volcano.read_report(xml(report(info_type='訂正'))), ISSUE_URL)
        self.assertNotEqual(original['hash'], corrected['hash'])
        self.assertIn('订正', corrected['title'])
        changed = deepcopy(base)
        changed['prevention'] += '修正'
        self.assertNotEqual(original['hash'], jma_volcano.make_event(changed, ISSUE_URL)['hash'])

    def test_duplicate_municipalities_are_collapsed_and_conflicting_states_fail(self):
        root = report()
        section = root.find('Body/VolcanoInfo[@type="' + jma_volcano.AREA_TYPE + '"]')
        section.append(deepcopy(section.find('Item')))
        self.assertEqual(len(jma_volcano.read_report(xml(root))['warning']['areas']), 4)
        section[-1].find('Kind/Code').text = '04'
        with self.assertRaisesRegex(ValueError, '冲突状态'):
            jma_volcano.read_report(xml(root))

    def test_invalid_current_codes_and_mismatched_event_ids_fail(self):
        for path, value in [('Body/VolcanoInfo/Item/Kind/Code', '06'),
                            ('Body/VolcanoInfo/Item/Areas/Area/Code', '315'),
                            ('Head/EventID', ''), ('Control/Status', 'unknown'),
                            ('Body/VolcanoInfo[@type="' + jma_volcano.AREA_TYPE + '"]/Item/Areas/Area/Code', '123')]:
            root = report()
            root.find(path).text = value
            with self.assertRaises(ValueError):
                jma_volcano.read_report(xml(root))

    def test_valid_reports_survive_another_failed_download(self):
        files = {jma.EQVOL_FEED_URL: feed([(ISSUE_URL, '1'), (CANCEL_URL, '2')]), ISSUE_URL: xml(report())}
        iterator = jma_volcano.events(files.__getitem__)
        self.assertEqual(next(iterator)['link'], ISSUE_URL)
        with self.assertRaisesRegex(RuntimeError, CANCEL_URL):
            next(iterator)

    def test_submission_levels_follow_warning_state_and_training_status(self):
        generated, levels = [], []
        for kind in jma_volcano.KINDS:
            for status in ('通常', '訓練', '試験'):
                for info_type in ('発表', '訂正', '取消'):
                    root = report(status=status, info_type=info_type)
                    root.find('Body/VolcanoInfo/Item/Kind/Code').text = kind
                    generated.append(jma_volcano.make_event(jma_volcano.read_report(xml(root)), ISSUE_URL))
                    levels.append(3 if status != '通常' or kind in ('11', '21', '35') else 4)
        with patch.object(jma_volcano, 'events', return_value=iter(generated)), \
                patch('core.database.create_event') as submit:
            jma_volcano.JMAVolcanoSpider().main()
        self.assertEqual([call.args[0] for call in submit.call_args_list], levels)
        self.assertTrue(all(call.args[2] == 'JMAVolcano' for call in submit.call_args_list))


if __name__ == '__main__':
    unittest.main()
