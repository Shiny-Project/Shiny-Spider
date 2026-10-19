from copy import deepcopy
import hashlib
from pathlib import Path
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from core import jma
from core.spider import Spider
from core.utils import load_spider
from spiders.weather import jma_eruption, jma_volcano
from test_jma_ew import feed


FIXTURES = Path(__file__).parent / 'fixtures' / 'jma'
# Unmodified samples from https://xml.kishou.go.jp/jmaxml_20260917_Samples.zip.
SAMPLES = ['67_01_0{}_140927_VFVO56.xml'.format(index) for index in range(1, 5)]
URL = 'https://example.test/1_0_VFVO56_010000.xml'


def report(index=0):
    return jma_eruption.parse_xml((FIXTURES / SAMPLES[index]).read_bytes())


def event(root, url=URL):
    return jma_eruption.make_event(jma_eruption.read_report(ET.tostring(root, encoding='utf-8')), url)


class EruptionTests(unittest.TestCase):
    def setUp(self):
        jma._cache.clear()

    def test_official_confirmed_suspected_correction_and_cancellation_samples(self):
        results = [event(report(index)) for index in range(4)]
        self.assertEqual([item['eruption'].get('kind') for item in results], ['52', '62', '62', None])
        self.assertIn('· 发生喷发', results[0]['title'])
        self.assertIn('· 疑似喷发', results[1]['title'])
        self.assertNotIn('· 发生喷发', results[1]['title'])
        self.assertEqual(results[0]['eruption']['time'], '2014-09-27T11:53:00+09:00')
        self.assertEqual(results[0]['eruption']['timeDubious'], '頃')
        self.assertIn('訂正', results[2]['eruption']['infoType'])
        self.assertEqual(results[2]['eruption']['time'], '2014-09-27T11:52:00+09:00')
        self.assertIn('噴火時刻を１１時５２分に修正', results[2]['content'])
        self.assertIn('电文取消', results[3]['title'])
        self.assertIn('噴火速報を取り消します', results[3]['content'])
        self.assertNotIn('time', results[3]['eruption'])
        self.assertNotIn('喷发时间', results[3]['content'])
        self.assertEqual(results[0]['eruption']['eventId'], '20140927120000_312')
        self.assertEqual(results[0]['eruption']['volcano'], {'code': '312', 'name': '御嶽山'})
        self.assertEqual(len(results[0]['eruption']['areas']), 4)
        self.assertNotIn('warning', results[0])
        for result in results:
            self.assertNotIn('喷发时间：', result['content'])
            self.assertNotIn('气象厅 ', result['content'])

    def test_official_samples_match_their_source_checksums(self):
        hashes = [
            'fca9c74721e73e8ffaf98f4c00dfc748dd6c6bc15ee51aa0f9bc73710ffdd3a0',
            'b90e97749b9e10dc7668205446962b6b227a4bcc9defa267c57e4777c7fc7278',
            '2093a4df85306fe26a7d6fa7a2d245915800e0b4d19d96e04a669284ea22d619',
            '307fd145fb7b494dd3090f4363eeb96aa3717c0755344e1460d5f695a786d0f1',
        ]
        for name, expected in zip(SAMPLES, hashes):
            self.assertEqual(hashlib.sha256((FIXTURES / name).read_bytes()).hexdigest(), expected)

    def test_cancellation_alone_needs_no_previous_report_or_structured_body(self):
        root = report(3)
        root.remove(root.find('Body'))
        files = {jma.EQVOL_FEED_URL: feed([(URL, '1')]), URL: ET.tostring(root)}
        result, = list(jma_eruption.events(files.__getitem__))
        self.assertEqual(result['eruption']['volcano']['name'], '御嶽山')
        self.assertIn('噴火速報を取り消します', result['content'])
        self.assertNotIn('kind', result['eruption'])

    def test_observation_time_uses_utc_or_target_time_without_inventing_unknown_times(self):
        root = report()
        item = root.find('Body/VolcanoInfo/Item')
        observed = item.find('EventTime')
        observed.remove(observed.find('EventDateTime'))
        self.assertEqual(event(root)['eruption']['time'], '2014-09-27T02:53:00Z')
        item.remove(observed)
        self.assertEqual(event(root)['eruption']['time'], '2014-09-27T11:53:00+09:00')
        root.find('Head').remove(root.find('Head/TargetDateTime'))
        result = event(root)
        self.assertNotIn('time', result['eruption'])
        self.assertNotIn('喷发时间', result['content'])

    def test_observation_precision_and_optional_notice_prevention_and_supplements(self):
        root = report()
        observed = root.find('Body/VolcanoInfo/Item/EventTime/EventDateTime')
        observed.set('significant', 'yyyy-mm-ddThh')
        content = root.find('Body/VolcanoInfoContent')
        for key, value in [('VolcanoPrevention', '警戒事項'), ('Appendix', '補足情報')]:
            ET.SubElement(content, key).text = value
        ET.SubElement(root.find('Body'), 'Notice').text = '訓練文です'
        result = event(root)
        self.assertEqual(result['eruption']['timePrecision'], 'yyyy-mm-ddThh')
        for value in ('警戒事項', '補足情報', '訓練文です'):
            self.assertIn(value, result['content'])

    def test_missing_body_can_use_headline_and_new_volcano_codes_need_no_position(self):
        root = report()
        root.remove(root.find('Body'))
        root.find('Head/EventID').text = '20140927120000_902'
        area = root.find('Head/Headline/Information/Item/Areas/Area')
        area.find('Code').text = '902'
        area.find('Name').text = '新たな活火山'
        result = event(root)
        self.assertEqual(result['eruption']['volcano'], {'code': '902', 'name': '新たな活火山'})
        self.assertNotIn('coordinate', result['eruption']['volcano'])
        self.assertIn('＜御嶽山で噴火が発生＞', result['content'])

    def test_feed_ignores_other_volcano_products_and_deduplicates_telegrams(self):
        duplicate = URL.replace('/1_', '/2_')
        other = URL.replace('VFVO56', 'VFVO50')
        files = {jma.EQVOL_FEED_URL: feed([(URL, '1'), (duplicate, '2'), (other, '3')]),
                 URL: (FIXTURES / SAMPLES[0]).read_bytes(), duplicate: (FIXTURES / SAMPLES[0]).read_bytes()}
        fetch = unittest.mock.Mock(side_effect=files.__getitem__)
        self.assertEqual(len(list(jma_eruption.events(fetch))), 1)
        self.assertNotIn(other, [call.args[0] for call in fetch.call_args_list])
        selected = jma_eruption.feed_entries(feed([
            (URL, '1'), (URL, '1'), (URL.replace('VFVO56', 'VFVO52'), '2'),
            (URL.replace('VFVO56', 'VFVO57'), '2')]))
        self.assertEqual(selected, [('1', URL)])

    def test_hash_is_stable_across_links_and_area_order_but_preserves_revisions(self):
        root = report()
        original = event(root)
        self.assertEqual(original['hash'], event(root, 'another-url')['hash'])
        areas = root.find('Body/VolcanoInfo[@type="噴火速報（対象市町村等）"]/Item/Areas')
        areas[:] = reversed(list(areas))
        areas.append(deepcopy(areas[0]))
        self.assertEqual(original['hash'], event(root)['hash'])
        self.assertEqual(len({event(report(index))['hash'] for index in range(4)}), 4)

    def test_scheduler_reuses_eqvol_downloads_without_mixing_in_vfvo50(self):
        other_url = URL.replace('VFVO56', 'VFVO50')
        files = {
            jma.EQVOL_FEED_URL: feed([(URL, '1'), (other_url, '2')]),
            URL: (FIXTURES / SAMPLES[0]).read_bytes(),
            other_url: (FIXTURES / '45_01_01_200522_VFVO50.xml').read_bytes(),
        }
        jma_volcano._previous_reports.clear()
        with patch.object(Spider, 'fetch', side_effect=files.__getitem__) as fetch, \
                patch('core.database.create_event') as submit:
            load_spider('weather/jma_eruption').JMAEruptionSpider().main()
            load_spider('weather/jma_volcano').JMAVolcanoSpider().main()
            load_spider('weather/jma_eruption').JMAEruptionSpider().main()
        self.assertEqual(fetch.call_count, 3)
        self.assertEqual([call.args[2] for call in submit.call_args_list], ['JMAEruption', 'JMAVolcano', 'JMAEruption'])
        self.assertEqual(submit.call_args_list[0].args[3], submit.call_args_list[2].args[3])

    def test_issuance_correction_cancellation_and_training_submission_levels(self):
        for status, expected in [('通常', 4), ('訓練', 3), ('試験', 3)]:
            generated = []
            for index in range(4):
                root = report(index)
                root.find('Control/Status').text = status
                generated.append(event(root))
            with patch.object(jma_eruption, 'events', return_value=iter(generated)), \
                    patch('core.database.create_event') as submit:
                jma_eruption.JMAEruptionSpider().main()
            self.assertEqual([call.args[0] for call in submit.call_args_list], [expected] * 4)
            for item in generated:
                self.assertNotIn('喷发时间：', item['content'])
                self.assertNotIn('气象厅 ', item['content'])
            if status != '通常':
                self.assertTrue(all(item['title'].startswith('【') for item in generated))

    def test_invalid_codes_event_ids_statuses_and_unzoned_times_are_rejected(self):
        for path, value in [('Head/EventID', '312'), ('Control/Status', 'other'),
                            ('Head/InfoType', '解除'), ('Control/DateTime', '2014-09-27T12:00:00'),
                            ('Body/VolcanoInfo/Item/Kind/Code', '13'),
                            ('Body/VolcanoInfo/Item/Areas/Area/Code', '306')]:
            root = report()
            root.find(path).text = value
            with self.assertRaises(ValueError):
                event(root)

    def test_valid_reports_are_submitted_even_when_another_download_fails(self):
        bad = URL.replace('/1_', '/2_')
        files = {jma.EQVOL_FEED_URL: feed([(bad, '1'), (URL, '2')]), URL: (FIXTURES / SAMPLES[0]).read_bytes()}
        iterator = jma_eruption.events(files.__getitem__)
        self.assertEqual(next(iterator)['link'], URL)
        with self.assertRaisesRegex(RuntimeError, bad):
            next(iterator)


if __name__ == '__main__':
    unittest.main()
