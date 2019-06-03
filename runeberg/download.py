#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Download a single book from Runeberg.org.

@TODO: handle/detect volumed works:
    ocr zip contains no Pages folder;
    images zip doesn't exist but r.status_code is still 200.
@TODO: handle colour images (both download and later insert/replace):
    quick first pass would be to download and check if `not is_empty_file()`
    if so then mention the existence of these to the user
    (later djvu would likely not work).
@TODO: Create update prompt for whether to overwrite downloaded files or not
@TODO: Consider dropping tqdm:
    Less useful as runeberg doesn't provide file size in header, but still
    indicates that something is happening (good for large files).
"""
import os
import shutil
import zipfile

import requests
from tqdm import tqdm

SITE = 'http://runeberg.org'
DATA_DIR = 'downloaded_data'
UNZIP_SUBDIR = 'tmp'
IMG_DIR = 'Images'


def exists_on_runeberg(uid):
    """
    Check if the work exists on Runeberg.org.

    This does not check if the provided title is that of a work or the landing
    page for a multi-volumed work.

    @param uid: the runeberg.org work identifier to look for
    @return: bool
    """
    url = '{0}/{1}/'.format(SITE, uid)
    r = requests.get(url)
    return r.status_code == 200


def is_empty_file(file_path):
    """
    Check if the provided file path is that of an empty (0 byte) file.

    @param file_path: the file path to check
    @return: bool
    """
    return os.stat(file_path).st_size == 0


def download_author_file(data_dir=None):
    """
    Download the runeberg.org author file to a.lst and convert it to utf-8.

    @param data_dir: the directory to which the data should be downloaded.
        Defaults to DATA_DIR.
    @return: path to downloaded file
    """
    return download_lst_file('a.lst', data_dir)


def download_works_file(data_dir=None):
    """
    Download the runeberg.org works file to t.lst and convert it to utf-8.

    @param data_dir: the directory to which the data should be downloaded.
        Defaults to DATA_DIR.
    @return: path to downloaded file
    """
    return download_lst_file('t.lst', data_dir)


def download_lst_file(file_name, data_dir=None):
    """
    Download a runeberg.org .lst file and convert it to utf-8.

    @param data_dir: the directory to which the data should be downloaded.
        Defaults to DATA_DIR.
    @param file_name: name of the file to download and to which it is saved.
    @return: path to downloaded file
    """
    data_dir = data_dir or DATA_DIR
    url = '{0}/authors/{1}'.format(SITE, file_name)
    output_file = os.path.join(os.getcwd(), data_dir, file_name)
    r = requests.get(url)
    r.encoding = 'latin1'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(r.text)
    return output_file


def get_work(uid, data_dir=None, sub_dir=None, img_dir=''):
    """
    Download, unzip and normalise all of the files related to a work.

    @param uid: the runeberg.org work identifier for the work to download
    @param data_dir: the name of the directory to which any data should be
        downloaded (a work specific subdirectory will be created). Defaults
        to cwd + DATA_DIR.
    @param sub_dir: the name of the sub-directory of 'data_dir' to which the
        files should be unzipped. Any files already in this directory will be
        deleted. Defaults to UNZIP_SUBDIR.
    @param img_dir: the name given to the image sub-directory. Defaults to
        IMG_DIR. Set to None to keep the non-standardised name.
    """
    data_dir = data_dir or DATA_DIR
    sub_dir = sub_dir or UNZIP_SUBDIR
    img_dir = IMG_DIR if img_dir == '' else img_dir
    work_dir = os.path.join(os.getcwd(), data_dir, uid)

    files = download_work(uid, work_dir, update=None)
    unzip_dir = unzip_work(files, sub_dir)
    normalise_unzipped_files(unzip_dir, img_dir)


def download_work(uid, work_dir, update=None):
    """
    Download all of the files related to a work.

    @param uid: the runeberg.org work identifier for the work to download
    @param work_dir: the path of the work specific sub-directory to which the
        data should be downloaded.
    @param update: whether to overwrite already downloaded files. Set to None
        to trigger a prompt.
    @return: list of paths to downloaded files
    """
    if not exists_on_runeberg(uid):
        raise NoSuchWorkError(uid)
    try:
        os.makedirs(work_dir, exist_ok=True)
    except OSError as e:
        raise DirCreationError(work_dir, e)

    urls = [
        ('ocr', '{0}/download.pl?mode=txtzip&work={1}'.format(SITE, uid)),
        ('images', '{0}/{1}.zip'.format(SITE, uid)),
        # ('colour', '{0}/download.pl?mode=jpgzip&work={1}'.format(SITE, title))
    ]

    files = []
    for label, url in urls:
        output_file = os.path.join(
            work_dir, '{0}_{1}.zip'.format(uid, label))

        # handle already downloaded files
        if not update and (os.path.isfile(output_file)
                           and not is_empty_file(output_file)):
            if update is None:
                raise NotImplementedError('Update prompt not implemented')
            else:
                continue

        r = requests.get(url, stream=True)
        with open(output_file, 'wb') as handle:
            for data in tqdm(r.iter_content(), desc=label, unit_scale=True, unit='B'):
                handle.write(data)
        files.append(output_file)
    return files


def unzip_work(files, sub_dir):
    """
    Unzip all of the downloaded files for a work to the given sub-directory.

    @param files: list of zip files to unpack
    @param sub_dir: the name of the sub-directory to which the files should be
        unzipped. Any files already in this directory will be deleted.
    @return: path to the directory in which the files were unzipped
    """
    work_dir = os.path.dirname(files[0])
    unzip_dir = os.path.join(work_dir, sub_dir)
    try:
        os.mkdir(unzip_dir)  # will raise FileExistsError if exists
    except FileExistsError:
        # overwrite old unzips to ensure newest data only
        shutil.rmtree(unzip_dir)
        os.mkdir(unzip_dir)

    for f in files:
        # non-existent files end up as 0 byte zips
        if is_empty_file(f):
            continue
        with zipfile.ZipFile(f, 'r') as zip_ref:
            zip_ref.extractall(unzip_dir)

    return unzip_dir


def normalise_unzipped_files(unzip_dir, img_dir):
    """
    Normalise the directory structure and file encoding of the unzipped files.

    The images are stored in a directory named after the work uid, this is
    renamed to ensure the same structure for all unzips.

    The metadata file is 'ISO-8859-1' encoded, this is changed to utf-8.

    @param unzip_dir: the path to the directory to which the files were
        unzipped.
    @param img_dir: the name given to the image directory. If None the
        non-standardised name is kept.
    """
    work_uid = os.path.basename(os.path.split(unzip_dir)[0])

    # normalise image directory
    if img_dir and os.path.isdir(os.path.join(unzip_dir, work_uid)):
        os.rename(
            os.path.join(unzip_dir, work_uid),
            os.path.join(unzip_dir, img_dir))

    # normalise metadata file encoding
    metadata_file = os.path.join(unzip_dir, 'Metadata')
    if os.path.isfile(metadata_file):
        re_encode_file(metadata_file, 'ISO-8859-1', 'utf-8')


def re_encode_file(input_file, from_codec, to_codec):
    """Change the encoding of a file."""
    output_file = '{}_tmp'.format(input_file)

    with open(input_file, encoding=from_codec) as f, \
            open(output_file, 'w', encoding=to_codec) as e:
        text = f.read()
        e.write(text)
    os.remove(input_file)
    os.rename(output_file, input_file)


class NoSuchWorkError(Exception):
    """Error raised when a work does not exist."""

    def __init__(self, uid):
        """Initialise the Error."""
        msg = 'The work "{0}" was not found on runeberg.org'.format(uid)
        super().__init__(msg)


class DirCreationError(Exception):
    """Error raised when directory creation fails."""

    def __init__(self, out_path, error):
        """Initialise the Error."""
        msg = 'Could not create the directory "{0}". Error: {1}'.format(
            out_path, error)
        super().__init__(msg)
