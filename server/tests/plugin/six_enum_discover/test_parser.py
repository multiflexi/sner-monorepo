# This file is part of sner4 project governed by MIT license, see the LICENSE.txt file.
"""
six_enum_discover output parser tests
"""

from sner.plugin.six_enum_discover.parser import ParserModule


def test_host_list():
    """check host list extraction"""

    expected_hosts = ['::1']

    pidb = ParserModule.parse_path('tests/server/data/parser-six_enum_discover-job.zip')

    assert [x.address for x in pidb.hosts] == expected_hosts
