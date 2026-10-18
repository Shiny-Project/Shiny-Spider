from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import time
import unittest
from unittest.mock import Mock, patch
import xml.etree.ElementTree as ET

from core import jma
from spiders.weather import jma_ew


FIXTURES = Path(__file__).parent / 'fixtures' / 'jma'
# 官方原样 XML：xml.kishou.go.jp/jmaxml_20260917_Samples.zip，及
# www.jma.go.jp/jma/kishou/know/bosai/keiho-update2026/tech-info/zip/
# 20260323_sample_timeline_{heavyrain,landslide,stormsurge}.zip。


def report(kinds=(), status='通常', info_type='発表', date='2026-10-17T01:00:00Z', body=True):
    root = ET.Element('Report', xmlns='http://xml.kishou.go.jp/jmaxml1/')
    control = ET.SubElement(root, 'Control')
    for key, value in [('Title', '気象警報・注意報（Ｒ０６）（大雨）'),
                       ('DateTime', date), ('Status', status), ('PublishingOffice', '横浜地方気象台')]:
        ET.SubElement(control, key).text = value
    head = ET.SubElement(root, 'Head')
    ET.SubElement(head, 'ReportDateTime').text = date
    ET.SubElement(head, 'InfoType').text = info_type
    if body:
        warning = ET.SubElement(ET.SubElement(root, 'Body'), 'Warning', type='気象警報・注意報（市町村等）')
        for code, state, area, previous in kinds:
            item = ET.SubElement(warning, 'Item')
            kind = ET.SubElement(item, 'Kind')
            ET.SubElement(kind, 'Code').text = code
            ET.SubElement(kind, 'Status').text = state
            if previous:
                ET.SubElement(ET.SubElement(kind, 'LastKind'), 'Code').text = previous
            area_node = ET.SubElement(item, 'Area')
            ET.SubElement(area_node, 'Code').text = area
            ET.SubElement(area_node, 'Name').text = {'1410011': '横浜市北部', '1410012': '横浜市南部'}.get(area, area)
    return ET.tostring(root, encoding='utf-8')


def feed(entries):
    root = ET.Element('feed', xmlns='http://www.w3.org/2005/Atom')
    for url, updated in entries:
        entry = ET.SubElement(root, 'entry')
        ET.SubElement(entry, 'id').text = url
        ET.SubElement(entry, 'link', href=url)
        ET.SubElement(entry, 'updated').text = updated
        ET.SubElement(ET.SubElement(entry, 'author'), 'name').text = '横浜地方気象台'
    return ET.tostring(root, encoding='utf-8')


class WarningTests(unittest.TestCase):
    def setUp(self):
        jma._cache.clear()
        jma_ew._previous_reports.clear()

    def test_official_r06_issue_and_downgrade_timelines(self):
        for code, issued, ended, count in [
            ('33', 'VPWW55_JPTF_170930.xml', 'VPWW55_JPTF_170932.xml', 35),
            ('39', 'VPWW56_JPTF_170930.xml', 'VPWW56_JPTF_170932.xml', 33),
            ('38', 'VPWW57_JPTF_160734.xml', 'VPWW57_JPTF_161105.xml', 16),
        ]:
            with self.subTest(code=code):
                issue = jma_ew.make_event(jma_ew.read_report((FIXTURES / issued).read_bytes()), issued)
                release = jma_ew.make_event(jma_ew.read_report((FIXTURES / ended).read_bytes()), ended)
                self.assertEqual(set(issue['warning']['active']), {code})
                self.assertEqual(len(issue['warning']['active'][code]), count)
                self.assertEqual(release['warning']['ended'][code], issue['warning']['active'][code])
                self.assertEqual(release['warning']['active'], {})
                self.assertIn('1410011', issue['warning']['active'][code])
                self.assertEqual(set(issue['warning']), {'active', 'ended', 'status', 'infoType'})

    def test_ordinary_danger_warning_does_not_become_an_emergency_warning(self):
        data = (FIXTURES / 'VPWW55_JPTF_170928.xml').read_bytes()
        self.assertIsNone(jma_ew.make_event(jma_ew.read_report(data), 'ordinary'))

    def test_current_transitional_53_and_54_structures(self):
        release = jma_ew.make_event(jma_ew.read_report(
            (FIXTURES / '15_09_03_130826_VPWW53.xml').read_bytes()), 'release')
        self.assertEqual(release['warning']['active'], {})
        self.assertEqual(set(release['warning']['ended']), {'33', '35', '37'})
        issue = jma_ew.make_event(jma_ew.read_report(
            (FIXTURES / '15_12_01_161130_VPWW54.xml').read_bytes()), 'issue')
        self.assertEqual(len(issue['warning']['active']['33']), 3)

    def test_all_seven_kinds_and_training_test_statuses(self):
        for code in jma_ew.KINDS:
            for status in ('通常', '訓練', '試験'):
                with self.subTest(code=code, status=status):
                    event = jma_ew.make_event(jma_ew.read_report(report(
                        [(code, '発表', '1410011', None)], status=status)), 'issue')
                    self.assertEqual(event['warning']['active'], {code: ['1410011']})
                    self.assertEqual(event['warning']['status'], status)

    def test_partial_release_and_overlapping_kinds_keep_correct_states(self):
        event = jma_ew.make_event(jma_ew.read_report(report([
            ('33', '継続', '1410011', '33'),
            ('43', '特別警報から危険警報', '1410012', '33'),
            ('05', '特別警報から警報', '1410011', '35'),
        ])), 'mixed')
        self.assertEqual(event['warning']['active'], {'33': ['1410011']})
        self.assertEqual(event['warning']['ended'], {'33': ['1410012'], '35': ['1410011']})
        self.assertIn('横浜市南部', event['content'])

    def test_direct_release_and_last_kind_change(self):
        event = jma_ew.make_event(jma_ew.read_report(report([
            ('33', '解除', '1410011', '33'),
            ('35', '発表', '1410012', '32'),
        ])), 'mixed')
        self.assertEqual(event['warning']['active'], {'35': ['1410012']})
        self.assertEqual(event['warning']['ended'], {'32': ['1410012'], '33': ['1410011']})

    def test_continuation_is_quiet_but_correction_is_not(self):
        kinds = [('33', '継続', '1410011', '33')]
        self.assertIsNone(jma_ew.make_event(jma_ew.read_report(report(kinds)), 'continued'))
        correction = jma_ew.make_event(jma_ew.read_report(report(kinds, info_type='訂正')), 'corrected')
        self.assertEqual(correction['warning']['infoType'], '訂正')
        self.assertIn('订正', correction['title'])

    def test_cancelled_telegram_uses_its_body_or_preceding_report(self):
        previous = jma_ew.read_report(report([('33', '発表', '1410011', None)]))
        for data in [report([('33', '発表', '1410011', None)], info_type='取消'),
                     report(info_type='取消', body=False)]:
            event = jma_ew.make_event(jma_ew.read_report(data), 'cancelled', previous)
            self.assertEqual(event['warning']['active'], {})
            self.assertEqual(event['warning']['ended'], {'33': ['1410011']})
            self.assertEqual(event['warning']['infoType'], '取消')
        self.assertIsNone(jma_ew.make_event(jma_ew.read_report(report(info_type='取消', body=False)), 'unrelated'))

    def test_feed_prefers_54_to_53_and_ignores_obsolete_and_aggregate_types(self):
        entries = [
            ('https://example.test/1_0_VPWW53_140000.xml', '2026-10-17T01:00:00Z'),
            ('https://example.test/1_0_VPWW54_140000.xml', '2026-10-17T01:00:00Z'),
            ('https://example.test/1_0_VPWW55_140000.xml', '2026-10-17T01:00:00Z'),
            ('https://example.test/2_0_VPWW53_140000.xml', '2026-10-17T01:01:00Z'),
            ('https://example.test/2_0_VPWW54_140000.xml', '2026-10-17T01:01:00Z'),
            ('https://example.test/2_0_VPWW50_140000.xml', '2026-10-17T01:01:00Z'),
            ('https://example.test/2_0_VPWW61_140000.xml', '2026-10-17T01:01:00Z'),
        ]
        selected = jma_ew.feed_entries(feed(entries))
        self.assertEqual([code for updated, code, url in selected], ['VPWW54', 'VPWW55', 'VPWW54'])

    def test_r06_and_transitional_telegrams_with_different_feed_times_are_not_submitted_twice(self):
        old = 'https://example.test/1_0_VPWW54_140000.xml'
        new = 'https://example.test/2_0_VPWW55_140000.xml'
        data = report([('33', '発表', '1410011', None)])
        files = {jma.FEED_URL: feed([(old, '2026-10-17T01:00:00Z'), (new, '2026-10-17T01:00:03Z')]),
                 old: data, new: data}
        result = list(jma_ew.events(files.__getitem__))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['link'], new)

    def test_feed_is_processed_oldest_first_and_bodyless_cancel_survives_next_poll(self):
        issue = 'https://example.test/1_0_VPWW55_140000.xml'
        cancel = 'https://example.test/2_0_VPWW55_140000.xml'
        files = {jma.FEED_URL: feed([(cancel, '2026-10-17T01:01:00Z'), (issue, '2026-10-17T01:00:00Z')]),
                 issue: report([('33', '発表', '1410011', None)]),
                 cancel: report(info_type='取消', date='2026-10-17T01:01:00Z', body=False)}
        result = list(jma_ew.events(files.__getitem__))
        self.assertEqual([item['warning']['infoType'] for item in result], ['発表', '取消'])
        jma._cache.clear()
        files[jma.FEED_URL] = feed([(cancel, '2026-10-17T01:01:00Z')])
        self.assertEqual(list(jma_ew.events(files.__getitem__))[0]['warning']['ended'], {'33': ['1410011']})

    def test_successful_reports_are_submitted_even_if_another_download_fails(self):
        good = 'https://example.test/1_0_VPWW55_140000.xml'
        bad = 'https://example.test/2_0_VPWW56_140000.xml'
        files = {jma.FEED_URL: feed([(good, '1'), (bad, '2')]),
                 good: report([('33', '発表', '1410011', None)])}
        iterator = jma_ew.events(files.__getitem__)
        self.assertEqual(next(iterator)['link'], good)
        with self.assertRaisesRegex(RuntimeError, bad):
            next(iterator)


class DownloadTests(unittest.TestCase):
    def setUp(self):
        jma._cache.clear()

    def test_separate_spiders_and_concurrent_requests_share_the_same_download(self):
        def download(url):
            time.sleep(0.02)
            return b'<Report />'
        fetch = Mock(side_effect=download)
        with ThreadPoolExecutor(6) as pool:
            self.assertEqual(list(pool.map(lambda _: jma.fetch_xml(jma.FEED_URL, fetch), range(6))), [b'<Report />'] * 6)
        fetch.assert_called_once_with(jma.FEED_URL)
        other_spider = Mock(side_effect=AssertionError('Second spider must reuse download'))
        self.assertEqual(jma.fetch_xml(jma.FEED_URL, other_spider), b'<Report />')

    def test_feed_refreshes_after_40_seconds_while_telegram_stays_cached(self):
        clock = [0]
        fetch = Mock(return_value=b'<Report />')
        url = 'https://example.test/telegram.xml'
        with patch('core.jma.monotonic', side_effect=lambda: clock[0]):
            jma.fetch_xml(jma.FEED_URL, fetch)
            jma.fetch_xml(jma.EQVOL_FEED_URL, fetch)
            jma.fetch_xml(url, fetch)
            clock[0] = 39
            jma.fetch_xml(jma.FEED_URL, fetch)
            jma.fetch_xml(jma.EQVOL_FEED_URL, fetch)
            self.assertEqual(fetch.call_count, 3)
            clock[0] = 40
            jma.fetch_xml(jma.FEED_URL, fetch)
            jma.fetch_xml(jma.EQVOL_FEED_URL, fetch)
            jma.fetch_xml(url, fetch)
            self.assertEqual(fetch.call_count, 5)

    def test_network_failures_and_invalid_xml_can_be_retried(self):
        fetch = Mock(side_effect=[OSError('network failed'), b'not xml', b'<Report />'])
        for error in (OSError, ET.ParseError):
            with self.assertRaises(error):
                jma.fetch_xml(jma.FEED_URL, fetch)
        self.assertEqual(jma.fetch_xml(jma.FEED_URL, fetch), b'<Report />')
        self.assertEqual(fetch.call_count, 3)


if __name__ == '__main__':
    unittest.main()
