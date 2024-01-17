# This file is part of sner4 project governed by MIT license, see the LICENSE.txt file.
"""
auth.views.profile selenium tests
"""

from base64 import b64decode, b64encode
from flask import url_for

from fido2 import cbor
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from soft_webauthn import SoftWebauthnDevice

from sner.server.auth.models import User
from sner.server.extensions import webauthn
from tests.selenium import webdriver_waituntil, frontend_url, wait_for_js
from tests.selenium.auth import js_variable_ready


def test_profile_route(live_server, sl_user, webauthn_credential_factory):  # pylint: disable=unused-argument
    """check profile page rendering"""

    wac = webauthn_credential_factory.create(user=User.query.filter_by(username='pytest_user').one())

    sl_user.get(frontend_url('/auth/profile'))
    wait_for_js(sl_user)
    webdriver_waituntil(sl_user, EC.visibility_of_element_located((By.XPATH, f'//td[contains(text(), "{wac.name}")]')))


def test_profile_webauthn_register_route(live_server, sl_user):  # pylint: disable=unused-argument
    """register new credential for user"""

    device = SoftWebauthnDevice()

    sl_user.get(frontend_url(url_for('auth.profile_webauthn_register_route')))
    wait_for_js(sl_user)
    # some javascript code must be emulated
    webdriver_waituntil(sl_user, js_variable_ready('window.pkcco_raw'))
    pkcco = cbor.decode(b64decode(sl_user.execute_script('return window.pkcco_raw;').encode('utf-8')))
    attestation = device.create(pkcco, f'https://{webauthn.rp.id}')
    buf = b64encode(cbor.encode(attestation)).decode('utf-8')
    sl_user.execute_script(f'setAttestation(getPackedAttestation(CBORDecode(base64ToArrayBuffer("{buf}"))));')
    # and back to standard test codeflow
    sl_user.find_element(By.XPATH, '//form[@id="webauthn_register_form"]//input[@name="name"]').send_keys('pytest token')
    sl_user.find_element(By.XPATH, '//form[@id="webauthn_register_form"]//input[@type="submit"]').click()

    user = User.query.filter(User.username == 'pytest_user').one()
    assert user.webauthn_credentials
