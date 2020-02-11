import unittest

from app.dead_link_exposer import DeadLinkExposer


class DeadLinkTest(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None

        self.base_url = "https://www.yegor256.com/"
        self.links_detector = DeadLinkExposer(self.base_url)

    def test_links_detector_report(self):
        self.links_detector.validate_urls()
        report_result = self.links_detector.get_report()

        self.assertEqual(67, report_result['total'])
        self.assertEqual(5, report_result['dead'])
