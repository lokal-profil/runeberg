# -*- coding: utf-8 -*-
import setuptools

with open("README.md", "r") as readme, open("CHANGES.md", "r") as changes:
    long_description = '{0}\n\n{1}'.format(readme.read(), changes.read())

setuptools.setup(
    name="runeberg",
    version="0.0.2",
    author="André Costa",
    author_email="lokal.profil@gmail.com",
    description="Library for working with works from Projekt Runeberg (Runeberg.org).",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lokal-profil/runeberg",
    packages=["runeberg"],
    include_package_data=True,
    install_requires=["beautifulsoup4", "html5lib", "requests", "tqdm"],
    keywords=['runeberg', 'libraries', 'literature'],
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "runeberg=runeberg.__main__:main",
        ]
    },
)
