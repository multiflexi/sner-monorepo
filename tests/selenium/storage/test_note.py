# This file is part of sner4 project governed by MIT license, see the LICENSE.txt file.
"""
selenium ui tests for storage.note component
"""

from flask import url_for

from sner.server.model.storage import Note
from tests.selenium import dt_inrow_delete, dt_rendered
from tests.selenium.storage import check_annotate


def test_note_list_route(live_server, sl_operator, test_note):  # pylint: disable=unused-argument
    """simple test ajaxed datatable rendering"""

    sl_operator.get(url_for('storage.note_list_route', _external=True))
    dt_rendered(sl_operator, 'note_list_table', test_note.comment)


def test_note_list_route_inrow_delete(live_server, sl_operator, test_note):  # pylint: disable=unused-argument
    """delete note inrow button"""

    sl_operator.get(url_for('storage.note_list_route', _external=True))
    dt_inrow_delete(sl_operator, 'note_list_table')
    assert not Note.query.get(test_note.id)


def test_note_list_route_annotate(live_server, sl_operator, test_note):  # pylint: disable=unused-argument
    """annotate test"""

    check_annotate(sl_operator, 'storage.note_list_route', 'note_list_table', test_note)
