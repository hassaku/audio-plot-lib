from unittest import TestCase
from audio_plot_lib.playable import plot
from pydub import AudioSegment
import numpy as np


def plot_with_all_options(data):
    return plot(data, ptype="overlay", duration=20, gains=[-2, -3],
        min_freq=130.813/2, max_freq=130.813*3,
        decimals=2, description=False, labels=["A", "B"], autoplay=False)


class TestPlayable(TestCase):
    def setUp(self):
        self.ndarray_data = np.array([np.arange(0, np.pi*2, 0.1), -1 * np.arange(0, np.pi*2, 0.1)]).T


    def test_plot_with_ndarray(self):
        ret = plot_with_all_options(self.ndarray_data)
        self.assertEqual(type(ret), AudioSegment)


    def test_plot_with_list(self):
        ret = plot_with_all_options(self.ndarray_data.tolist())
        self.assertEqual(type(ret), AudioSegment)

