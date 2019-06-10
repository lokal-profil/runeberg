# runeberg  [![Build Status](https://travis-ci.org/lokal-profil/runeberg.svg?branch=master)](https://travis-ci.org/lokal-profil/runeberg)[![codecov.io Code Coverage](https://img.shields.io/codecov/c/github/lokal-profil/runeberg.svg?maxAge=2592000)](https://codecov.io/github/lokal-profil/runeberg?branch=master)

A library for downloading and parsing works from [Projekt Runeberg](http://runeberg.org).

## Usage

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
