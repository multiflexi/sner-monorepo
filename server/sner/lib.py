# This file is part of sner4 project governed by MIT license, see the LICENSE.txt file.
"""
shared functions
"""

import os
import signal
from contextlib import contextmanager
from pathlib import Path
from zipfile import ZipFile

import magic
import yaml


def load_yaml(filename):
    """load yaml from file, silence file not found"""

    if filename and os.path.exists(filename):
        config = yaml.safe_load(Path(filename).read_text(encoding='utf-8'))
        return config or {}
    return {}


def is_zip(path):
    """detect if path is zip archive"""
    return magic.detect_from_filename(path).mime_type == 'application/zip'


def file_from_zip(zippath, filename):
    """exctract filename data from zipfile"""

    with ZipFile(zippath) as ftmp_zip:
        with ftmp_zip.open(filename) as ftmp:
            return ftmp.read()


def format_host_address(value):
    """format ipv4 vs ipv6 address to string"""
    return value if ':' not in value else f'[{value}]'


class TerminateContextMixin:  # pylint: disable=too-few-public-methods
    """terminate context mixin"""

    @contextmanager
    def terminate_context(self):
        """terminate context manager; should restore handlers despite of underlying code exceptions"""

        self.original_signal_handlers[signal.SIGTERM] = signal.signal(signal.SIGTERM, self.terminate)
        self.original_signal_handlers[signal.SIGINT] = signal.signal(signal.SIGINT, self.terminate)
        try:
            yield
        finally:
            signal.signal(signal.SIGINT, self.original_signal_handlers[signal.SIGINT])
            signal.signal(signal.SIGTERM, self.original_signal_handlers[signal.SIGTERM])


def get_nested_key(data, *keys):
    """get nested key from dict"""

    try:
        for key in keys:
            data = data[key]
        return data
    except KeyError:
        return None
