# -*- coding: utf-8 -*-
import setuptools

version = "0.0.1"
with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="runeberg",
    version=version,
    author="André Costa",
    author_email="lokal.profil@gmail.com",
    description="Library for working with works from Projekt Runeberg (Runeberg.org).",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lokal-profil/runeberg",
    download_url='https://github.com/lokal-profil/runeberg/tarball/' + version,
    packages=["runeberg"],
    # include_package_data=True,
    install_requires=["beautifulsoup4", "html5lib", "requests", "tqdm"],
    keywords=['runeberg', 'libraries', 'literature'],
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
