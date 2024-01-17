# This file is part of sner4 project governed by MIT license, see the LICENSE.txt file.
"""
agent basic tests
"""

import json
from pathlib import Path
from uuid import uuid4

from flask import url_for

from sner.agent.core import main as agent_main
from sner.lib import file_from_zip
from sner.server.scheduler.models import Job, Queue


def test_version(tmpworkdir):  # pylint: disable=unused-argument
    """test print version"""

    result = agent_main(['--version'])
    assert result == 0


def test_commandline_assignment(tmpworkdir):  # pylint: disable=unused-argument
    """test custom assignment passed from command line"""

    test_a = {'id': str(uuid4()), 'config': {'module': 'dummy', 'args': '--arg1'}, 'targets': []}

    result = agent_main(['--assignment', json.dumps(test_a)])
    assert result == 0
    assert Path(f'{test_a["id"]}.zip').exists()


def test_exception_in_module(tmpworkdir):  # pylint: disable=unused-argument
    """test exception handling during agent module execution"""

    test_a = {'id': str(uuid4()), 'config': {'module': 'notexist'}, 'targets': []}

    result = agent_main(['--assignment', json.dumps(test_a)])
    assert result == 1
    assert Path(f'{test_a["id"]}.zip').exists()


def test_run_with_liveserver(tmpworkdir, live_server, apikey_agent, dummy_target):  # pylint: disable=unused-argument
    """test basic agent's networking codepath; fetch, execute, pack and upload assignment"""

    result = agent_main([
        '--server', url_for('index_route', _external=True),
        '--apikey', apikey_agent,
        '--queue', Queue.query.get(dummy_target.queue_id).name,
        '--caps', 'cap1', 'cap2',
        '--oneshot',
        '--debug',
    ])
    assert result == 0

    job = Job.query.filter(Job.queue_id == dummy_target.queue_id).one()
    assert dummy_target.target in file_from_zip(job.output_abspath, 'assignment.json').decode('utf-8')
