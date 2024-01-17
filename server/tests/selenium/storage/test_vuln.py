# This file is part of sner4 project governed by MIT license, see the LICENSE.txt file.
"""
selenium ui tests for storage.vuln component
"""

import string
from flask import url_for

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from sner.lib import format_host_address
from sner.server.extensions import db
from sner.server.storage.models import Vuln
from tests.selenium import dt_inrow_delete, dt_rendered, dt_count_rows, dt_wait_processing, webdriver_waituntil, frontend_url, wait_for_js
from tests.selenium.storage import (
    check_annotate,
    check_dt_toolbox_freetag,
    check_dt_toolbox_multiactions,
    check_dt_toolbox_select_rows,
    check_service_endpoint_dropdown
)


def check_vulns_filtering(sclnt, dt_id):
    """test vuln views filtering functions"""

    toolbar_id = f'{dt_id}_toolbar'

    # there should be 4 rows in total
    dt_elem = dt_wait_processing(sclnt, dt_id)
    assert len(dt_elem.find_elements(By.XPATH, './/tbody/tr')) == 4

    # one not tagged
    sclnt.find_element(By.ID, toolbar_id).find_element(By.XPATH, '//a[text()="Not tagged"]').click()
    dt_elem = dt_wait_processing(sclnt, dt_id)
    assert len(dt_elem.find_elements(By.XPATH, './/tbody/tr')) == 1
    assert dt_elem.find_element(By.XPATH, './/td/a[text()="vuln 1"]')

    # three tagged
    sclnt.find_element(By.ID, toolbar_id).find_element(By.XPATH, '//a[text()="Tagged"]').click()
    dt_elem = dt_wait_processing(sclnt, dt_id)
    assert len(dt_elem.find_elements(By.XPATH, './/tbody/tr')) == 3
    assert not dt_elem.find_elements(By.XPATH, './/td/a[text()="vuln 1"]')

    # two already reviewed
    sclnt.find_element(By.ID, toolbar_id).find_element(By.XPATH, '//a[text()="Exclude reviewed"]').click()
    dt_elem = dt_wait_processing(sclnt, dt_id)
    assert len(dt_elem.find_elements(By.XPATH, './/tbody/tr')) == 2
    assert dt_elem.find_element(By.XPATH, './/td/a[text()="vuln 1"]')
    assert dt_elem.find_element(By.XPATH, './/td/a[text()="vuln 2"]')

    # one should go directly to report
    sclnt.find_element(By.ID, toolbar_id).find_element(By.XPATH, '//a[text()="Only Report"]').click()
    dt_elem = dt_wait_processing(sclnt, dt_id)
    assert len(dt_elem.find_elements(By.XPATH, './/tbody/tr')) == 1
    assert dt_elem.find_element(By.XPATH, './/td/a[text()="vuln 4"]')

    # and user must be able to loose the filter
    sclnt.find_element(By.XPATH, '//a[text()="Unfilter"]').click()
    dt_elem = dt_wait_processing(sclnt, dt_id)
    assert len(dt_elem.find_elements(By.XPATH, './/tbody/tr')) == 4


def test_vuln_list_route(live_server, sl_operator, vuln):  # pylint: disable=unused-argument
    """simple test ajaxed datatable rendering"""

    sl_operator.get(frontend_url('/storage/vuln/list'))
    wait_for_js(sl_operator)
    dt_rendered(sl_operator, 'vuln_list_table', vuln.comment)


def test_vuln_list_route_inrow_delete(live_server, sl_operator, vuln):  # pylint: disable=unused-argument
    """delete vuln inrow button"""

    vuln_id = vuln.id
    db.session.expunge(vuln)

    sl_operator.get(frontend_url('/storage/vuln/list'))
    wait_for_js(sl_operator)
    dt_inrow_delete(sl_operator, 'vuln_list_table')

    assert not Vuln.query.get(vuln_id)


def test_vuln_list_route_annotate(live_server, sl_operator, vuln):  # pylint: disable=unused-argument
    """test annotation from list route"""

    sl_operator.get(frontend_url('/storage/vuln/list'))
    wait_for_js(sl_operator)
    dt_rendered(sl_operator, 'vuln_list_table', vuln.comment)
    check_annotate(sl_operator, 'vuln_comment_annotate', vuln)


def test_vuln_list_route_selectrows(live_server, sl_operator, vulns_multiaction):  # pylint: disable=unused-argument
    """test dt selection and selection buttons"""

    check_dt_toolbox_select_rows(sl_operator, frontend_url('/storage/vuln/list'), 'vuln_list_table')


def test_vuln_list_route_dt_toolbox_multiactions(live_server, sl_operator, vulns_multiaction):  # pylint: disable=unused-argument
    """test vulns multiactions"""

    check_dt_toolbox_multiactions(sl_operator, frontend_url('/storage/vuln/list'), 'vuln_list_table', Vuln)


def test_vuln_list_route_dt_toolbox_freetag(live_server, sl_operator, vulns_multiaction):  # pylint: disable=unused-argument
    """test dt freetag buttons"""

    check_dt_toolbox_freetag(sl_operator, frontend_url('/storage/vuln/list'), 'vuln_list_table', Vuln)


def test_vuln_list_route_filtering(live_server, sl_operator, vulns_filtering):  # pylint: disable=unused-argument
    """test list vulns view filtering features"""

    sl_operator.get(frontend_url('/storage/vuln/list'))
    wait_for_js(sl_operator)
    check_vulns_filtering(sl_operator, 'vuln_list_table')


def test_vuln_list_route_service_endpoint_dropdown(live_server, sl_operator, vuln_factory, service):  # pylint: disable=unused-argument
    """service endpoint uris dropdown test"""

    test_vuln = vuln_factory.create(service=service)

    sl_operator.get(frontend_url('/storage/vuln/list'))
    wait_for_js(sl_operator)
    dt_rendered(sl_operator, 'vuln_list_table', test_vuln.comment)
    check_service_endpoint_dropdown(
        sl_operator,
        sl_operator.find_element(By.ID, 'vuln_list_table'),
        f'{test_vuln.service.port}/{test_vuln.service.proto}'
    )

    sl_operator.find_element(By.XPATH, '//i[@title="Copy to clipboard"]').click()
    # readText is not supported in firefox
    # clipboard_text = sl_operator.execute_script('return navigator.clipboard.readText()')


def test_vuln_list_route_moredata_dropdown(live_server, sl_operator, vuln):  # pylint: disable=unused-argument
    """moredata dropdown test"""

    sl_operator.get(frontend_url('/storage/vuln/list'))
    wait_for_js(sl_operator)
    dt_rendered(sl_operator, 'vuln_list_table', vuln.comment)
    sl_operator.find_element(By.ID, 'vuln_list_table').find_element(
        By.XPATH,
        './/div[contains(@class, "dropdown")]/a[@title="Show more data"]'
    ).click()
    webdriver_waituntil(sl_operator, EC.visibility_of_element_located((
        By.XPATH,
        '//table[@id="vuln_list_table"]//h6[text()="More data"]'
    )))


def test_vuln_list_route_viatarget_visibility_toggle(live_server, sl_operator, vuln):  # pylint: disable=unused-argument
    """viatarget visibility toggle"""

    sl_operator.get(frontend_url('/storage/vuln/list'))
    wait_for_js(sl_operator)
    dt_rendered(sl_operator, 'vuln_list_table', vuln.comment)

    webdriver_waituntil(sl_operator, EC.invisibility_of_element_located((By.XPATH, '//th[contains(text(), "via_target")]')))

    sl_operator.find_element(By.XPATH, '//a[@id="dropdownUser"]').click()
    webdriver_waituntil(sl_operator, EC.visibility_of_element_located((By.XPATH, '//a[contains(text(), "Toggle via_target (false)")]')))
    sl_operator.find_element(By.XPATH, '//a[contains(text(), "Toggle via_target (false)")]').click()
    wait_for_js(sl_operator)
    dt_rendered(sl_operator, 'vuln_list_table', vuln.comment)

    webdriver_waituntil(sl_operator, EC.visibility_of_element_located((By.XPATH, '//th[contains(text(), "via_target")]')))


def test_vuln_view_route_tagging(live_server, sl_operator, vuln):  # pylint: disable=unused-argument
    """test vuln view tagging features"""

    assert 'info' not in vuln.tags

    sl_operator.get(frontend_url(f'/storage/vuln/view/{vuln.id}'))
    wait_for_js(sl_operator)
    sl_operator.find_element(By.XPATH, '//a[@data-testid="tag-btn" and text()="Info"]').click()
    webdriver_waituntil(
        sl_operator, EC.visibility_of_element_located((By.XPATH, '//span[contains(@class, "tag-badge") and contains(text(), "info")]'))
    )

    db.session.refresh(vuln)
    assert 'info' in Vuln.query.get(vuln.id).tags


def test_vuln_view_route_annotate(live_server, sl_operator, vuln):  # pylint: disable=unused-argument
    """test vuln annotation from view route"""

    sl_operator.get(frontend_url(f'/storage/vuln/view/{vuln.id}'))
    wait_for_js(sl_operator)
    check_annotate(sl_operator, 'vuln_comment_annotate', vuln)


def test_vuln_view_route_service_endpoint_dropdown(live_server, sl_operator, vuln_factory, service):  # pylint: disable=unused-argument
    """test note annotation from view route"""

    test_vuln = vuln_factory.create(service=service)

    sl_operator.get(frontend_url(f'/storage/vuln/view/{test_vuln.id}'))
    wait_for_js(sl_operator)
    check_service_endpoint_dropdown(
        sl_operator,
        sl_operator.find_element(By.XPATH, '//td[contains(@class, "service_endpoint_dropdown")]'),
        f'<Service {test_vuln.service.id}: {format_host_address(test_vuln.host.address)} {test_vuln.service.proto}.{test_vuln.service.port}>'
    )


def test_vuln_view_route_moredata_dropdown(live_server, sl_operator, vuln):  # pylint: disable=unused-argument
    """test vuln view breadcrumb ribbon moredata dropdown"""

    sl_operator.get(frontend_url(f'/storage/vuln/view/{vuln.id}'))
    wait_for_js(sl_operator)
    sl_operator.find_element(By.XPATH, '//div[contains(@class, "breadcrumb-buttons")]').find_element(
        By.XPATH,
        './/div[contains(@class, "dropdown")]/a[@title="Show more data"]'
    ).click()
    webdriver_waituntil(sl_operator, EC.visibility_of_element_located((
        By.XPATH,
        '//div[contains(@class, "breadcrumb-buttons")]//h6[text()="More data"]'
    )))


def test_vuln_grouped_route(live_server, sl_operator, vuln):  # pylint: disable=unused-argument
    """test grouped vulns view"""

    sl_operator.get(frontend_url('/storage/vuln/grouped'))
    wait_for_js(sl_operator)
    dt_wait_processing(sl_operator, 'vuln_grouped_table')
    assert dt_count_rows(sl_operator, 'vuln_grouped_table') == 1


def test_vuln_grouped_route_filtering(live_server, sl_operator, vulns_filtering):  # pylint: disable=unused-argument
    """test grouped vulns view filtering features"""

    sl_operator.get(frontend_url('/storage/vuln/grouped'))
    wait_for_js(sl_operator)
    check_vulns_filtering(sl_operator, 'vuln_grouped_table')


def test_vuln_grouped_route_filter_specialchars(live_server, sl_operator, vuln_factory):  # pylint: disable=unused-argument
    """test grouped vulns view and filtering features with specialchars"""

    vuln_factory.create(name=string.printable)

    sl_operator.get(frontend_url('/storage/vuln/grouped'))
    wait_for_js(sl_operator)
    elem_xpath = f"//a[contains(text(), '{string.digits}')]"
    webdriver_waituntil(sl_operator, EC.visibility_of_element_located((By.XPATH, elem_xpath)))

    sl_operator.find_element(By.XPATH, elem_xpath).click()
    dt_wait_processing(sl_operator, 'vuln_list_table')

    assert dt_count_rows(sl_operator, 'vuln_list_table') == 1


def test_vuln_edit_route_autocomplete(live_server, sl_operator, vuln, host_factory, service_factory):  # pylint: disable=unused-argument
    """test vuln addedit autocompletes"""

    host = host_factory.create(address='127.9.9.9')
    service = service_factory.create(host=host, port=993)

    assert vuln.host_id != host.id
    assert vuln.service_id != service.id

    sl_operator.get(frontend_url(url_for('storage.vuln_edit_route', vuln_id=vuln.id)))
    wait_for_js(sl_operator)
    sl_operator.find_element(By.XPATH, '//a[@data-toggle="collapse"]').click()

    elem_hostid_xpath = '//input[@name="host_id"]'
    webdriver_waituntil(sl_operator, EC.visibility_of_element_located((By.XPATH, elem_hostid_xpath)))
    elem_hostid = sl_operator.find_element(By.XPATH, elem_hostid_xpath)
    elem_hostid.clear()
    elem_hostid.send_keys(host.address[0])
    elem_xpath = f'//ul[@data-testid="host-autocomplete-list"]/li[text()="{host.address} (hostname: {host.hostname} id:{host.id})"]'
    webdriver_waituntil(sl_operator, EC.visibility_of_element_located((By.XPATH, elem_xpath)))
    sl_operator.find_element(By.XPATH, elem_xpath).click()

    elem_serviceid_xpath = '//input[@name="service_id"]'
    webdriver_waituntil(sl_operator, EC.visibility_of_element_located((By.XPATH, elem_serviceid_xpath)))
    elem_serviceid = sl_operator.find_element(By.XPATH, elem_serviceid_xpath)
    elem_serviceid.clear()
    elem_serviceid.send_keys(str(service.port)[:2])
    elem_xpath = '//ul[@data-testid="service-autocomplete-list"]/li' \
        f'[text()="{service.proto}/{service.port} {host.address} (hostname: {host.hostname} id:{host.id})"]'
    webdriver_waituntil(sl_operator, EC.visibility_of_element_located((By.XPATH, elem_xpath)))
    sl_operator.find_element(By.XPATH, elem_xpath).click()

    sl_operator.find_element(By.XPATH, '//form[@id="vuln_form"]//input[@type="submit"]').click()

    db.session.refresh(vuln)
    assert vuln.host_id == host.id
    assert vuln.service_id == service.id


def test_vuln_multicopy_route(live_server, sl_operator, vuln, host_factory, service_factory):  # pylint: disable=unused-argument
    """test vuln multicopy route"""

    host = host_factory.create(address='127.9.9.9')
    service = service_factory.create(host=host, port=993)

    sl_operator.get(frontend_url(f'/storage/vuln/multicopy/{vuln.id}'))
    wait_for_js(sl_operator)
    dt_wait_processing(sl_operator, 'vuln_multicopy_endpoints_table')
    sl_operator.find_element(By.XPATH, f'//table[@id="vuln_multicopy_endpoints_table"]/tbody/tr/td[text()="{service.port}"]').click()

    sl_operator.find_element(By.XPATH, '//form[@id="vuln_form"]//input[@type="submit"]').click()
    dt_elem = dt_wait_processing(sl_operator, 'vuln_list_table')

    assert len(dt_elem.find_elements(By.XPATH, './/tbody/tr')) == 2
    assert Vuln.query.filter(Vuln.host_id == host.id, Vuln.service_id == service.id, Vuln.xtype == vuln.xtype).one()
