# This file is part of sner4 project governed by MIT license, see the LICENSE.txt file.
"""
server functions tests
"""

import os
import re
import sys
from datetime import datetime
from io import StringIO
from unittest.mock import patch

import pytest
from flask import current_app

from sner.server.app import cli, create_app
from sner.version import __version__


def test_datetime_filter(app):
    """test datetime jinja filter"""

    assert app.jinja_env.filters['datetime'](datetime.strptime('2000-01-01T00:00:00', '%Y-%m-%dT%H:%M:%S')) == '2000-01-01T00:00:00'
    assert app.jinja_env.filters['datetime'](None) == ''


def test_json_indent_filter(app):
    """test indenting filter"""

    assert app.jinja_env.filters['json_indent']('"xxx"') == '"xxx"'
    assert app.jinja_env.filters['json_indent']('xxx') == 'xxx'


def test_from_json__filter(app):
    """test indenting filter"""

    assert app.jinja_env.filters['from_json']('"xxx"') == 'xxx'


def test_shell():
    """test shell context imports"""

    buf_stdin = StringIO('print(db.session)\n')
    buf_stdout = StringIO()

    patch_argv = patch.object(sys, 'argv', ['bin/server', 'shell'])
    patch_environ = patch.object(os, 'environ', {})
    patch_stdin = patch.object(sys, 'stdin', buf_stdin)
    patch_stdout = patch.object(sys, 'stdout', buf_stdout)
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        with patch_argv, patch_environ, patch_stdin, patch_stdout:
            cli()

    assert pytest_wrapped_e.value.code == 0
    assert 'sqlalchemy.orm.scoping.scoped_session' in buf_stdout.getvalue()


def test_cli():
    """test sner server cli/main flask wrapper"""

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        with patch.object(sys, 'argv', ['dummy']):
            with patch.object(os, 'environ', {}):
                cli()
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0


def test_version():
    """test sner server cli/main flask wrapper"""

    buf_stdout = StringIO()

    patch_argv = patch.object(sys, 'argv', ['--version', '--debug'])
    patch_environ = patch.object(os, 'environ', {})
    patch_stdout = patch.object(sys, 'stdout', buf_stdout)
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        with patch_argv, patch_environ, patch_stdout:
            cli()

    assert pytest_wrapped_e.value.code == 0
    assert f'Sner {__version__}' in buf_stdout.getvalue()


def test_logformatter(caplog):
    """test log formatter"""

    app = create_app(config_file='tests/sner.yaml')
    caplog.handler.setFormatter(app.logger.handlers[0].formatter)  # pylint: disable=no-member

    with app.app_context():
        current_app.logger.info('test1')
        assert re.match(r'^sner.server - - - \[.*\] INFO test1', caplog.text)
    caplog.clear()

    with app.test_request_context(environ_base={'REMOTE_ADDR': '127.0.0.2'}):
        current_app.logger.info('test2')
        assert re.match(r'^sner.server 127.0.0.2 - - \[.*\] INFO test2', caplog.text)
    caplog.clear()
