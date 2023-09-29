#!/usr/bin/env python
# encoding: utf-8

from __future__ import with_statement
from setuptools import setup

with open("README.md") as f:
    long_description = f.read()

setup(
    name="audio-plot-lib",
    version="0.1.1",
    description="Plot tools based on audio",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="hassaku",
    author_email="hassaku.apps@gmail.com",
    url="https://github.com/hassaku/audio-plot-lib",
    packages=["audio_plot_lib"],
    include_package_data=True,
    install_requires=["pydub==0.24.1", "numpy", "gTTS==2.2.1", "bokeh==2.4.3", "ipython"],
    tests_require=[],
    license="MIT",
    keywords="audio plot visually-impaired",
    zip_safe=False,
    classifiers=[]
)
