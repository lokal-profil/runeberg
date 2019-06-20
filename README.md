# runeberg  [![Build Status](https://travis-ci.org/lokal-profil/runeberg.svg?branch=master)](https://travis-ci.org/lokal-profil/runeberg)[![codecov.io Code Coverage](https://img.shields.io/codecov/c/github/lokal-profil/runeberg.svg)](https://codecov.io/github/lokal-profil/runeberg?branch=master)

A library and command line application for downloading and parsing works from
[Projekt Runeberg](http://runeberg.org).

## Installation

You can install the Runeberg from [PyPI](https://pypi.org/project/runeberg/):

    pip install runeberg

It is supported on Python 3.6 and above.

## Usage as a command line application

After installing `runeberg` simply call the program to get a paged output of
works to download, follow the prompts to download (and unpack) the files.
```console
$ runeberg
1. "Det Ringer!" Skämt i en akt (1902) by Helena Nyblom [sv]
2. "Då sa' kungen..." : Kungliga anekdoter under hundra år (1946) by ? [sv]
3. "Pastoralier" (1899) by August Olsson [sv]
4. "The Ripper" (uppskäraren) (1892) by Adolf Paul [sv]
5. 100 Præstehistorier eller Præstestandens lyse og mørke Sider (1893) by Nils Poulsen [no]
6. 14 Descriptive Pieces for the Young for Piano (1895) by Sveinbjörn Sveinbjörnsson [en]
7. 14 sovjetryska berättare : valda och översatta från ryskan (1929) by ? [sv]
8. 16 år med Roald Amundsen. Fra Pol til Pol (1930) by Oscar Wisting [no]
9. 1720, 1772, 1809 (1836) by Magnus Crusenstolpe [sv]
…
What do you want to do? [1–25] to download, [N]ext 25, [Q]uit: █
```

Use the `-a` flag to start with a list of authors for which a filtered list of
works will be presented:
```console
$ runeberg -a
1. Ülev Aaloe (1944) [ee]
2. Simon Aberstén (1865–1937) [se]
3. Selma Abrahamsson (1872–1911) [fi]
4. Arthur Dyke Acland (1847–1926) [uk]
5. Adam Bremensis (1044–1080) [de]
6. Gertrud Adelborg (1853–1942) [se]
7. Ottilia Adelborg (1855–1936) [se]
8. Gudmund Jöran Adlerbeth (1751–1818) [se]
9. Gustav Magnus Adlercreutz (1775–1845) [se]
…
What do you want to do? [1–25] to display their works, [N]ext 25, [Q]uit: 6
Displaying works by Gertrud Adelborg [uid=adelbger]…
1. Några drag af de till Danmark utvandrade allmogeflickornas ställning och arbetsförhållanden (1890) by Gertrud Adelborg [sv]
2. Några upplysningar angående de svenska allmogeflickornas utvandring till Danmark (1893) by Gertrud Adelborg [sv]
What do you want to do? [1–2] to download, [Q]uit: █
```

Use the `-h` flag to see a full list of options and filters.

## Usage as a library

First determine the identifier of the work you wish to download. For e.g.
<http://runeberg.org/aldrigilif/> this `<uid>` would be `aldrigilif`.
```python
# Download and unpack a work from runeberg.org:
# this will by default download the work to /downloaded_data/<uid>/
import runeberg.download as downloader

downloader.get_work('<uid>')
# Warning raised if additional colour images are found, these are not unpacked.

# Parse the downloaded work:
# from the parsed work you can access individual pages, articles/chapters along
# with any metadata
import runeberg
parsed_work = runeberg.Work.from_files('<uid>')

# Create a DjVu file of the work
print(parsed_work.to_djvu())  # outputs the path to the created file
```

## Caveats

Some of the `Metadata` files are encoded in `Windows 1252` rather than the
default `latin-1`. The framework does not currently detect this. If you
encounter such a file some characters may be misinterpreted and you must
manually re-encode the file before parsing the work.

If the originally scanned images were `.jpg` then the downloaded "colour
images" will just be a second identical copy of these.

## Requirements

For DjVu conversion `DjVuLibre` must be installed.
