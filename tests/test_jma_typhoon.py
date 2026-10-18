from pathlib import Path
import unittest
from unittest.mock import patch

from bs4 import BeautifulSoup
from core import jma
from core.spider import Spider
from spiders.weather.jma_typhoon import JMATyphoonSpider
from test_jma_ew import feed


FIXTURES = Path(__file__).parent / 'fixtures' / 'jma'
# Unmodified official XML from xml.kishou.go.jp/jmaxml_20260917_Samples.zip.
NORMAL = '10_04_03_170913_VPTW60.xml'
ENDED = '10_05_05_200826_VPTW61.xml'


def read_sample(name):
    return BeautifulSoup((FIXTURES / name).read_bytes(), 'xml', from_encoding='utf-8')


class TyphoonTests(unittest.TestCase):
    def setUp(self):
        jma._cache.clear()
        self.spider = JMATyphoonSpider()

    def submit_sample(self, name):
        url = 'https://example.test/' + name
        files = {jma.FEED_URL: feed([(url, '1')]), url: (FIXTURES / name).read_bytes()}
        with patch.object(Spider, 'fetch', side_effect=files.__getitem__), \
                patch('core.database.create_event') as submit:
            self.spider.main()
        self.assertEqual(submit.call_count, 1)
        level, data, publisher, event_hash = submit.call_args[0]
        self.assertEqual((level, publisher), (3, 'JMATyphoon'))
        return data

    def test_official_forecast_centers_and_all_twelve_radii_survive_submission(self):
        data = self.submit_sample(NORMAL)
        estimates = data['typhoon_data']['estimations']
        self.assertEqual(len(estimates), 13)
        circles = [point['probability_circle'] for point in estimates if 'probability_circle' in point]
        self.assertEqual([circle['radius'] for circle in circles],
                         ['30', '40', '60', '70', '80', '90', '100', '110', '200', '310', '480', '650'])
        expected = []
        for node in read_sample(NORMAL).find_all('ProbabilityCircle'):
            expected.append(node.find('BasePoint', attrs={'type': '中心位置（度）'}).get_text())
        self.assertEqual([circle['base_point'] for circle in circles], expected)
        self.assertIn('近中心最大风力', data['content'])

    def test_probability_circle_selects_degrees_and_kilometers_within_the_forecast_circle(self):
        report = read_sample(NORMAL)
        probability = report.find('ProbabilityCircle')
        degrees = probability.find('BasePoint', attrs={'type': '中心位置（度）'})
        expected = degrees.get_text()
        minutes = probability.find('BasePoint', attrs={'type': '中心位置（度分）'})
        minutes.extract()
        degrees.insert_before(minutes)
        unrelated = report.new_tag('jmx_eb:Radius', attrs={'unit': 'km'})
        unrelated.string = '999'
        probability.insert_before(unrelated)
        item = probability.find_parent('MeteorologicalInfo')
        result = self.spider.parse_typhoon_info(item)
        self.assertEqual(result['probability_circle'], {'base_point': expected, 'radius': '30'})

    def test_official_development_unlikely_report_without_wind_speed_is_submitted(self):
        data = self.submit_sample(ENDED)
        self.assertNotIn('near_center_wind_speed', data['typhoon_data']['current'])
        self.assertIn('发展为台风的可能性已减小', data['content'])
        self.assertIn('最后一次报告', data['content'])
        self.assertNotIn('最大风力', data['content'])

    def test_optional_wind_and_pressure_are_omitted_without_inventing_values(self):
        current = self.spider.parse_typhoon_info(read_sample(NORMAL).find('MeteorologicalInfo'))
        for missing in [('near_center_wind_speed',), ('pressure',), ('near_center_wind_speed', 'pressure')]:
            with self.subTest(missing=missing):
                partial = dict(current)
                for field in missing:
                    partial.pop(field, None)
                content = self.spider.generate_content({'current': partial})
                if 'near_center_wind_speed' in missing:
                    self.assertNotIn('最大风力', content)
                if 'pressure' in missing:
                    self.assertNotIn('中心气压', content)
                self.assertNotIn('None', content)
                self.assertIn('当前位于', content)


if __name__ == '__main__':
    unittest.main()
