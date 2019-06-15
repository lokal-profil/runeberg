# -*- coding: utf-8 -*-
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="runeberg",
    version="0.0.1",
    author="André Costa",
    author_email="lokal.profil@gmail.com",
    description="Library for working with works from Projekt Runeberg (Runeberg.org).",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lokal-profil/runeberg",
    packages=["runeberg"],
    install_requires=["beautifulsoup4", "html5lib", "requests", "tqdm"],
    keywords=['runeberg', 'libraries', 'literature'],
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "runeberg=runeberg.__main__:main",
        ]
    },
)
