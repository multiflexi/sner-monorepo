# This file is part of sner4 project governed by MIT license, see the LICENSE.txt file.
"""
selenium ui tests for scheduler.job component
"""

import json

from selenium.webdriver.common.by import By

from sner.server.extensions import db
from sner.server.scheduler.models import Heatmap, Job, Target
from tests.selenium import dt_inrow_delete, dt_rendered, dt_wait_processing, frontend_url, wait_for_js


def test_job_list_route(live_server, sl_operator, job):  # pylint: disable=unused-argument
    """simple test ajaxed datatable rendering"""

    sl_operator.get(frontend_url('/scheduler/job/list'))
    wait_for_js(sl_operator)
    dt_rendered(sl_operator, 'job_list_table', job.id)


def test_job_list_route_inrow_delete(live_server, sl_operator, job_completed):  # pylint: disable=unused-argument
    """delete job inrow button"""

    job_id = job_completed.id
    db.session.expunge(job_completed)

    sl_operator.get(frontend_url('/scheduler/job/list'))
    wait_for_js(sl_operator)
    dt_inrow_delete(sl_operator, 'job_list_table')
    assert not Job.query.get(job_id)


def test_job_list_route_inrow_reconcile(live_server, sl_operator, job):  # pylint: disable=unused-argument
    """job list inrow reconcile button"""

    assert Heatmap.query.filter(Heatmap.count > 0).count() == 2

    dt_id = 'job_list_table'
    sl_operator.get(frontend_url('/scheduler/job/list'))
    wait_for_js(sl_operator)
    dt_wait_processing(sl_operator, dt_id)
    sl_operator.find_element(By.ID, dt_id).find_element(By.XPATH, '//a[@data-testid="reconcile-btn"]').click()
    dt_wait_processing(sl_operator, dt_id)

    assert job.retval == -1
    assert Heatmap.query.filter(Heatmap.count > 0).count() == 0


def test_job_list_route_inrow_repeat(live_server, sl_operator, job):  # pylint: disable=unused-argument
    """job list inrow repeat button"""

    dt_id = 'job_list_table'
    sl_operator.get(frontend_url('/scheduler/job/list'))
    wait_for_js(sl_operator)
    dt_wait_processing(sl_operator, dt_id)
    sl_operator.find_element(By.ID, dt_id).find_element(By.XPATH, '//a[@data-testid="repeat-btn"]').click()
    dt_wait_processing(sl_operator, dt_id)

    assert len(json.loads(job.assignment)['targets']) == Target.query.count()
