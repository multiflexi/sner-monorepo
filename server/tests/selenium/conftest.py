# This file is part of sner4 project governed by MIT license, see the LICENSE.txt file.
"""
shared fixtures for selenium tests
"""

import pytest
from flask import url_for
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from sner.server.auth.models import User
from sner.server.extensions import db
from sner.server.password_supervisor import PasswordSupervisor as PWS
from tests.selenium import webdriver_waituntil, wait_for_js, frontend_url


@pytest.fixture
def firefox_options(firefox_options):  # pylint: disable=redefined-outer-name
    """override firefox options"""

    firefox_options.headless = True
    return firefox_options


def selenium_in_roles(sclnt, roles):
    """create user role and login selenium to role(s)"""

    tmp_password = PWS.generate()
    tmp_user = User(username='pytest_user', password=PWS.hash(tmp_password), active=True, roles=roles)
    db.session.add(tmp_user)
    db.session.commit()

    sclnt.get(frontend_url(url_for('auth.login_route')))
    wait_for_js(sclnt)
    sclnt.find_element(By.XPATH, '//form//input[@name="username"]').send_keys(tmp_user.username)
    sclnt.find_element(By.XPATH, '//form//input[@name="password"]').send_keys(tmp_password)
    sclnt.find_element(By.XPATH, '//form//input[@type="submit"]').click()
    webdriver_waituntil(sclnt, EC.presence_of_element_located((By.XPATH, '//a[text()="Logout"]')))

    return sclnt


@pytest.fixture
def sl_user(selenium):  # pylint: disable=redefined-outer-name
    """yield client authenticated to role user"""

    yield selenium_in_roles(selenium, ['user'])


@pytest.fixture
def sl_operator(selenium):  # pylint: disable=redefined-outer-name
    """yield client authenticated to role operator"""

    yield selenium_in_roles(selenium, ['user', 'operator'])


@pytest.fixture
def sl_admin(selenium):  # pylint: disable=redefined-outer-name
    """yield client authenticated to role admin"""

    yield selenium_in_roles(selenium, ['user', 'operator', 'admin'])
