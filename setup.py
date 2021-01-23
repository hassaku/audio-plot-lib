#!/usr/bin/env python
# encoding: utf-8

from __future__ import with_statement
from setuptools import setup

with open("README.md") as f:
    long_description = f.read()

setup(
    name="audio-plot-lib",
    version="0.0.5",
    description="Plot tools based on audio",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="hassaku",
    author_email="hassaku.apps@gmail.com",
    url="https://github.com/hassaku/audio-plot-lib",
    packages=["audio_plot_lib"],
    include_package_data=True,
    install_requires=["pydub", "numpy", "gTTS", "bokeh"],
    tests_require=["nose", "mock"],
    license="MIT",
    keywords="audio plot visually-impaired",
    zip_safe=False,
    classifiers=[]
)
