import asyncio
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Lock
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import Main
from core import config, database
from core.spider import Spider
from Shiny import ShinyError


class StopPolling(Exception):
    pass


def job(job_id):
    return {'id': job_id, 'spider': 'Test', 'path': 'example/example', 'info': {}}


class SchedulerTests(unittest.TestCase):
    def run_batch(self, jobs, workers, before_sleep=None):
        def sleep(seconds):
            self.assertEqual(seconds, 15)
            if before_sleep is not None:
                before_sleep()
            raise StopPolling

        with patch.object(config, 'SPIDER_CONCURRENCY', workers), \
                patch.object(Main.database, 'get_job_list', return_value=jobs) as poll, \
                patch.object(Main.time, 'sleep', side_effect=sleep), \
                patch.object(Main, 'Logger'):
            with self.assertRaises(StopPolling):
                Main.start_spiders()
        poll.assert_called_once_with()

    def test_jobs_overlap_within_limit_and_all_finish_before_next_poll(self):
        barrier = Barrier(2)
        lock = Lock()
        active = 0
        maximum = 0
        completed = []

        def renew(job_id, spider_name, path, info):
            nonlocal active, maximum
            with lock:
                active += 1
                maximum = max(maximum, active)
            barrier.wait(timeout=5)
            with lock:
                completed.append(job_id)
                active -= 1

        def check_finished():
            self.assertEqual(sorted(completed), [1, 2, 3, 4])
            self.assertEqual(active, 0)

        with patch.object(Main, 'renew', side_effect=renew):
            self.run_batch([job(i) for i in range(1, 5)], 2, check_finished)
        self.assertEqual(maximum, 2)

    def test_one_worker_preserves_submission_order(self):
        completed = []
        with patch.object(Main, 'renew', side_effect=lambda job_id, *args, **kwargs: completed.append(job_id)):
            self.run_batch([job(3), job(1), job(2)], 1)
        self.assertEqual(completed, [3, 1, 2])

    def test_failed_spider_does_not_prevent_other_jobs_or_status_reports(self):
        failed = SimpleNamespace(main=Mock(side_effect=RuntimeError('download failed')))
        good = SimpleNamespace(main=Mock())
        duplicate = SimpleNamespace(main=Mock(side_effect=ShinyError('already exists', code='duplicated_item')))
        module = SimpleNamespace(
            FailedSpider=Mock(return_value=failed),
            GoodSpider=Mock(return_value=good),
            DuplicateSpider=Mock(return_value=duplicate),
        )
        jobs = [dict(job(i), spider=name) for i, name in enumerate(('Failed', 'Good', 'Duplicate'), 1)]
        with patch.object(Main.utils, 'load_spider', return_value=module), \
                patch.object(Main.database, 'report_job_status') as report:
            self.run_batch(jobs, 2)
        self.assertCountEqual([call[0] for call in report.call_args_list],
                              [(1, 'failed'), (2, 'success'), (3, 'success')])
        good.main.assert_called_once_with()

    def test_empty_or_failed_poll_still_waits(self):
        for jobs in ([], None):
            with self.subTest(jobs=jobs), patch.object(Main, 'renew') as renew:
                self.run_batch(jobs, 2)
                renew.assert_not_called()


class WorkerCompatibilityTests(unittest.TestCase):
    def test_fetch_many_creates_and_closes_a_loop_for_each_worker_call(self):
        loops = []

        class AsyncSpider(Spider):
            async def do_fetch_tasks(self, urls):
                loops.append(asyncio.get_running_loop())
                return await asyncio.gather(*(self.fetch_one(url) for url in urls))

            async def fetch_one(self, url):
                await asyncio.sleep(0)
                return 'response:' + url

        with ThreadPoolExecutor(max_workers=1) as executor:
            for _ in range(2):
                result = executor.submit(AsyncSpider().fetch_many, ['first', 'second']).result(timeout=5)
                self.assertEqual(result, ['response:first', 'response:second'])
        self.assertIsNot(loops[0], loops[1])
        self.assertTrue(all(loop.is_closed() for loop in loops))

    def test_sdk_connections_and_cookies_are_isolated_between_workers(self):
        client = database._ShinySession()
        barrier = Barrier(2)

        def request(worker):
            client.session.cookies.set('worker', worker)
            barrier.wait(timeout=5)
            return client.session, client.session.cookies.get('worker')

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(request, worker) for worker in ('first', 'second')]
            results = [future.result(timeout=5) for future in futures]
        self.assertIsNot(results[0][0], results[1][0])
        self.assertEqual([result[1] for result in results], ['first', 'second'])
        self.assertIsNone(client.session.cookies.get('worker'))
        for session, cookie in results:
            session.close()
        client.session.close()

    def test_sdk_get_and_post_keep_request_timeouts(self):
        client = database._ShinySession()
        with patch.object(client.session, 'request') as request:
            client.get('https://example.test/jobs', headers={'test': 'value'})
            request.assert_called_with('GET', 'https://example.test/jobs',
                                       headers={'test': 'value'}, timeout=config.SHINY_REQUEST_TIMEOUT)
            client.post('https://example.test/report', {'status': 'success'}, timeout=2)
            request.assert_called_with('POST', 'https://example.test/report',
                                       data={'status': 'success'}, timeout=2)
        client.session.close()


if __name__ == '__main__':
    unittest.main()
