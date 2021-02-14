from unittest import TestCase
from audio_plot_lib.interactive import plot
import numpy as np
from unittest.mock import patch

def plot_with_all_options(data):
    plot(y=data, x=data, label=[0, 0, 1], width=100, height=100, title="title")


class TestInteractive(TestCase):
    def setUp(self):
        self.ndarray_data = np.ones((3, 1))


    def test_plot_with_ndarray(self):
        with patch('audio_plot_lib.interactive.show') as mock_show:
            plot_with_all_options(self.ndarray_data)
            self.assertTrue(mock_show.called)


    def test_plot_with_list(self):
        with patch('audio_plot_lib.interactive.show') as mock_show:
            plot_with_all_options(self.ndarray_data.tolist())
            self.assertTrue(mock_show.called)

