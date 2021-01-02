import copy
import numpy as np
from pydub import AudioSegment
from pydub.generators import Sine, Pulse, Square, Sawtooth, Triangle, WhiteNoise
from gtts import gTTS
from IPython.display import Audio, display


def __tts(utter: str):
    tts = gTTS(utter)
    tts.save("tmp.mp3")
    return AudioSegment.from_mp3("tmp.mp3")


def __sample(freq: float):
    return Sine(freq).to_audio_segment(duration=1000).apply_gain(-10).fade_in(20).fade_out(20)


def __overlay_plot(tones, lines, labels, min_freq, min_value, tic, duration, gains):
    assert lines.shape[1] <= 5, "The maximum number of lines is 5. (lines.shape[1] <= 5)"

    for t in range(lines.shape[1]):
        tones += __tts("{} is {} sound".format(labels[t], ["Sine", "Pulse", "Square", "Sawtooth", "Triangle"][t]))

    __tones = None
    for t in range(lines.shape[1]):
        __tones_t = AudioSegment.silent(duration=0)
        __duration = int(duration/4)

        for x, y in enumerate(lines[:, t]):
            gen = [Sine, Pulse, Square, Sawtooth, Triangle][t](min_freq + (y - min_value) * tic)
            wav = gen.to_audio_segment(duration=duration).apply_gain(gains[t])
            wav = wav.fade_in(__duration).fade_out(__duration).pan(-1.0 + x / lines.shape[0]*2)
            __tones_t += wav

        if __tones is None:
            __tones = __tones_t
        else:
            __tones = __tones.overlay(__tones_t)

    return tones + __tones


def __sequential_plot(tones, lines, labels, min_freq, min_value, tic, duration, gains):
    for t in range(lines.shape[1]):
        tones += __tts(labels[t])
        __duration = int(duration/4)

        for x, y in enumerate(lines[:, t]):
            gen = Sine(min_freq + (y - min_value) * tic)
            sine = gen.to_audio_segment(duration=duration).apply_gain(gains[t])
            sine = sine.fade_in(__duration).fade_out(__duration).pan(-1.0 + x / lines.shape[0] * 2)
            tones += sine

    return tones


def plot(lines: np.array, labels: list=None, ptype: str="sequential", duration: int=50, gain: int=-5, gains: list=None,
        min_freq: float=130.813, max_freq: float=130.813*4, decimals: int=1, description: bool=True, autoplay: bool=True) -> AudioSegment:
    """Plots that represent data with sound and can be checked by only audio

    Play back the data given in the array as sound in order.
    The value is expressed by the pitch of the sound.

    Parameters
    ----------
    lines : np.array
        A numpy array of values to be graphed.
        If you have two types of data, you need to align them
        to the same length and pass them as a two-dimensional array.
        The rows are the data length and the columns are the data type.
    labels: list
        The name of the data to be read out. Optional.
    ptype: str
        The default "sequential" will play back multiple data in order when multiple data are available,
        while the "overlay" will play back multiple data at the same time.
        Default is sequential.
    duration: int
        Length of each note.
        Default is 50 msec.
    gain: int
        Volume of sound applied commonly.
        Default is -5 dB.
    gains: list
        Volumes of each sound. Optional.
    min_freq: float
        The lowest frequency, corresponding to the minimum value.
        Default is 130.813 Hz
    max_freq: float
        The highest frequency, corresponding to the maximum value.
        Default is 130.813*4 Hz
    decimals: int
        Read out floating point.
        Default is 1
    description: bool
        Whether to read out loud or not.
        Default is true
    autoplay: bool
        Whether to play immediately after execution.
        Default is true

    Examples
    --------
    >>> plot(np.arange(0, np.pi*2, 0.1))
    <IPython.lib.display.Audio object>
    >>> plot(np.array([np.arange(0, np.pi*2, 0.1), -1 * np.arange(0, np.pi*2, 0.1)]).T,\
            ptype="overlay", duration=20, gains=[-2, -3], min_freq=130.813/2, max_freq=130.813*3,\
            decimals=2, description=False, labels=["A", "B"])
    <IPython.lib.display.Audio object>
    """

    if type(lines) == list:
        lines = np.array(copy.copy(lines))

    assert lines.ndim in [1, 2], "numpy array lines.ndim must be 1 or 2"
    if lines.ndim == 2:
        assert lines.shape[0] > lines.shape[1], "lines.shape must be time and lines each"
    else:
        lines = copy.copy(lines).reshape((-1, 1))

    if labels is None:
        labels = ["line {}".format(l+1) for l in range(lines.shape[1])]
    else:
        assert len(labels) == lines.shape[1], "len(labels) must equal lines.shape[1]"

    if gains is None:
        gains = [gain for _ in range(lines.shape[1])]
    else:
        assert len(gains) == lines.shape[1], "len(gains) must equal lines.shape[1]"

    min_value = np.nanmin(lines)
    max_value = np.nanmax(lines)
    tic = (max_freq - min_freq) / (max_value - min_value)

    tones = AudioSegment.silent(duration=0)

    if description:
        # describe yaxis
        tones += __tts("minimum value is {}".format(np.round(min_value, decimals)))
        tones += __sample(min_freq)
        tones += __tts("maximum value is {}".format(np.round(max_value, decimals)))
        tones += __sample(max_freq)

    # plot lines
    if ptype == "sequential":
        tones = __sequential_plot(tones, lines, labels, min_freq, min_value, tic, duration, gains)
    elif ptype == "overlay":
        tones = __overlay_plot(tones, lines, labels, min_freq, min_value, tic, duration, gains)
    else:
        raise NotImplementedError("ptype must be sequential or overlay")

    if autoplay:
        display(Audio(tones.get_array_of_samples(), rate=tones.frame_rate*2, autoplay=True))

    else:
        return tones

