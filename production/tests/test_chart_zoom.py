import unittest

from fastest_chart import chart_with_labels


class ReleaseChartZoomTest(unittest.TestCase):
    def test_standalone_chart_exposes_zoom_controls_and_retains_label_toggle(self):
        chart = chart_with_labels('<svg viewBox="0 0 100 100"></svg>', left=10, right=90, start=0, end=100)
        self.assertIn('aria-label="Chart zoom"', chart)
        self.assertIn('data-chart-zoom="reset"', chart)
        self.assertIn('Show point labels', chart)
        self.assertIn('data-chart-zoom-script', chart)
