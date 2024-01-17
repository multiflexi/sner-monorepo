# This file is part of sner4 project governed by MIT license, see the LICENSE.txt file.
"""
auth default tests
"""

import os
from http import HTTPStatus
from pathlib import Path
from time import time

from flask import url_for
from requests.utils import dict_from_cookiejar


def create_timedout_session(clnt):
    """creates timed out session"""

    sid = clnt.app.session_interface._generate_sid()  # pylint: disable=protected-access
    session_path = os.path.join(clnt.app.session_interface.storage, sid)

    os.makedirs(clnt.app.session_interface.storage)
    Path(session_path).write_text('{}', encoding='utf-8')
    timedout = time() - clnt.app.session_interface.max_idle_time - 1
    os.utime(session_path, (timedout, timedout))

    return sid, session_path


def test_timedout_session(client):
    """test timed out session"""

    sid, session_path = create_timedout_session(client)
    client.app.session_interface.gc_probability = 0.0  # gc collector must not interfere

    response = client.get(url_for('index_route'), headers={'cookie': f'session={sid}'})
    assert response.status_code == HTTPStatus.OK
    assert sid != dict_from_cookiejar(client.cookiejar)['session']
    assert not os.path.exists(session_path)


def test_notexist_session(client):
    """test non-existent session id handling"""

    sid = client.app.session_interface._generate_sid()  # pylint: disable=protected-access
    response = client.get(url_for('index_route'), headers={'cookie': f'session={sid}'})
    assert response.status_code == HTTPStatus.OK
    assert sid != dict_from_cookiejar(client.cookiejar)['session']


def test_gc_session(client):
    """test gc on session storage"""

    _, session_path = create_timedout_session(client)
    client.app.session_interface.gc_probability = 1.0  # gc collector must run

    response = client.get(url_for('index_route'))
    assert response.status_code == HTTPStatus.OK
    assert not os.path.exists(session_path)
