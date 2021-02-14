# audio-plot-lib

![Python package](https://github.com/hassaku/audio-plot-lib/workflows/Python%20package/badge.svg)

This library provides graph sonification functions
 and has been developed for a project named "Data science and machine learning resources for screen reader users".
 Please refer to the project page for more details.

https://hassaku.github.io/DS-and-ML-with-screen-reader/

# Use in Google Colab (recommended)

Try the following example.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/hassaku/audio-plot-lib/blob/master/audio_plot_lib_example.ipynb)

# Use in script (option)

## Interactive

Generate html with graphs that can be displayed interactively in a browser.

### Dependency

```
$ pip install audio-plot-lib
$ pip install beautifulsoup4
```

### Example

```
import audio_plot_lib as apl
apl.interactive.plot([0, 1, 2, 3, 2, 1, 0], script_name=__file__)
```

Open the html file with the same name as the script name in your browser, and if you find a button that reads 'push here to unmute graph', try moving the mouse cursor appropriately after pressing the button. If not, try reloading the page.

## Playable

Generate an audio file with sonified graphs.

### Dependency

```
$ sudo apt-get install libavformat-dev libavfilter-dev libavdevice-dev ffmpeg
$ pip install audio-plot-lib
```

### Example

```
import audio_plot_lib as apl
from pydub.playback import play

# generate graph sound
audio = apl.playable.plot([0, 1, 2, 3, 2, 1, 0], duration=300, autoplay=False)

# play
play(audio)

# save to audio file
audio.export("graph.wav", format="wav")
```

# For contributer

## Update PyPI

```
$ python -m unittest discover tests
$ pip install twine # if necessary
$ cat ~/.pypirc  # if necessary
[distutils]
index-servers = pypi

[pypi]
repository: https://upload.pypi.org/legacy/
username: YOUR_USERNAME
password: YOUR_PASSWORD
$ rm -rf audio-plot-lib.egg-info dist # if necessary
$ python setup.py sdist
$ twine upload --repository pypi dist/*
$ pip --no-cache-dir install --upgrade audio-plot-lib
```

https://pypi.org/project/audio-plot-lib/

## Contributing

- Fork the repository on Github
- Create a named feature branch (like add_component_x)
- Write your change
- Write tests for your change (if applicable)
- Run the tests, ensuring they all pass
- Submit a Pull Request using Github

# License

MIT
