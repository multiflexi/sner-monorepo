# This file is part of sner4 project governed by MIT license, see the LICENSE.txt file.
"""
tests agent fixtures
"""

import re
import os
import signal
from uuid import uuid4

import pytest


@pytest.fixture
def cleanup_markedprocess():
    """will cleanup markedprocess from failed testcase"""

    yield
    procs_list = os.popen('ps -f').read().splitlines()
    marked_procs = list(filter(lambda x: 'MARKEDPROCESS' in x, procs_list))
    marked_procs_pids = list(map(lambda x: int(re.split(r' +', x, maxsplit=7)[1]), marked_procs))
    for pid in marked_procs_pids:
        os.kill(pid, signal.SIGTERM)


@pytest.fixture
def dummy_a():
    """test dummy assignment"""

    yield {
        'id': str(uuid4()),
        'module': 'dummy',
        'config': '--static_assignment',
        'targets': ['target1']
    }


@pytest.fixture
def longrun_a():
    """longrun assignment fixture"""

    yield {
        'id': str(uuid4()),
        'module': 'nmap',
        'config': '-Pn --reason -sT --max-rate 1 --data-string MARKEDPROCESS',
        'targets': ['127.0.0.127']
    }


@pytest.fixture
def dummy_target(dummy_a, queue_factory, target_factory):  # pylint: disable=redefined-outer-name
    """dummy target fixture"""

    queue = queue_factory.create(name='testqueue', module=dummy_a['module'], config=dummy_a['config'])
    target = target_factory.create(queue=queue, target=dummy_a['targets'][0])
    yield target


@pytest.fixture
def longrun_target(longrun_a, queue_factory, target_factory):  # pylint: disable=redefined-outer-name
    """queue target fixture"""

    queue = queue_factory.create(name='testqueue', module=longrun_a['module'], config=longrun_a['config'])
    target = target_factory.create(queue=queue, target=longrun_a['targets'][0])
    yield target
