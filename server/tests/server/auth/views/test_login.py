# This file is part of sner4 project governed by MIT license, see the LICENSE.txt file.
"""
auth.views.login tests
"""

from base64 import b64decode, b64encode
from http import HTTPStatus
from unittest.mock import Mock, patch

from authlib.common.errors import AuthlibBaseError
from fido2 import cbor
from flask import current_app, redirect, url_for
from soft_webauthn import SoftWebauthnDevice

from sner.server.auth.core import TOTPImpl
from sner.server.extensions import oauth, webauthn
from sner.server.password_supervisor import PasswordSupervisor as PWS
from tests.server import get_csrf_token


def test_session_login(client, user_factory):
    """test login"""

    password = PWS.generate()
    user = user_factory.create(password=PWS.hash(password))

    form_data = [('username', user.username), ('password', 'invalid'), ('csrf_token', get_csrf_token(client))]
    response = client.post(url_for('auth.login_route'), params=form_data, expect_errors=True)

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json["error"]["message"] == "Invalid credentials."

    form_data = [('username', user.username), ('password', password), ('csrf_token', get_csrf_token(client))]
    response = client.post(url_for('auth.login_route'), params=form_data)

    assert response.status_code == HTTPStatus.OK


def test_session_logout(cl_user):
    """test logout"""

    response = cl_user.get(url_for('auth.logout_route'))
    assert response.status_code == HTTPStatus.OK
    assert response.json["message"] == "Successfully logged out."


def test_session_forbidden(cl_user):
    """access forbidden"""

    response = cl_user.get(url_for('auth.user_list_json_route'), status='*')
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_login_totp(client, user_factory):
    """test login totp"""

    password = PWS.generate()
    secret = TOTPImpl.random_base32()
    user = user_factory(password=PWS.hash(password), totp=secret)

    form_data = [('username', user.username), ('password', password)]
    response = client.post(url_for('auth.login_route'), params=form_data)
    assert response.status_code == HTTPStatus.OK

    form_data = [('code', 'invalid')]
    response = client.post(url_for('auth.login_totp_route'), params=form_data, expect_errors=True)
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json["error"]["message"] == "Invalid code."

    response = client.post(url_for('auth.login_totp_route'), expect_errors=True)
    assert response.status_code == HTTPStatus.BAD_REQUEST

    form_data = [('code', TOTPImpl(secret).current_code())]
    response = client.post(url_for('auth.login_totp_route'), params=form_data)
    assert response.status_code == HTTPStatus.OK


def test_login_totp_unauthorized(client):
    """test unauthorized login totp"""

    form_data = [('code', 'invalid')]
    response = client.post(url_for('auth.login_totp_route'), params=form_data, expect_errors=True)
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_login_webauthn(client, webauthn_credential_factory):
    """test login by webauthn"""

    device = SoftWebauthnDevice()
    device.cred_init(webauthn.rp.id, b'randomhandle')
    wncred = webauthn_credential_factory.create(initialized_device=device)

    form_data = [('username', wncred.user.username)]
    response = client.post(url_for('auth.login_route'), params=form_data)
    assert response.status_code == HTTPStatus.OK
    assert response.json["webauthn_login"]

    # some javascript code muset be emulated
    pkcro = cbor.decode(b64decode(client.post(url_for('auth.login_webauthn_pkcro_route')).body))
    assertion = device.get(pkcro, f'https://{webauthn.rp.id}')
    assertion_data = {
        'credentialRawId': assertion['rawId'],
        'authenticatorData': assertion['response']['authenticatorData'],
        'clientDataJSON': assertion['response']['clientDataJSON'],
        'signature': assertion['response']['signature'],
        'userHandle': assertion['response']['userHandle']}

    form_data = [('assertion', b64encode(cbor.encode(assertion_data)))]
    response = client.post(url_for('auth.login_webauthn_route'), params=form_data)

    # and back to standard test codeflow
    assert response.status_code == HTTPStatus.OK


def test_login_webauthn_unauthorized(client):
    """test unauthorized login webauthn"""

    response = client.post(url_for('auth.login_webauthn_route'), expect_errors=True)
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_login_webauthn_invalid_request(client, webauthn_credential_factory):
    """test invalid login webauthn"""

    device = SoftWebauthnDevice()
    device.cred_init(webauthn.rp.id, b'randomhandle')
    wncred = webauthn_credential_factory.create(initialized_device=device)

    form_data = [('username', wncred.user.username)]
    response = client.post(url_for('auth.login_route'), params=form_data)
    assert response.status_code == HTTPStatus.OK
    assert response.json["webauthn_login"]

    response = client.post(url_for('auth.login_webauthn_route'), expect_errors=True)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_profile_webauthn_pkcro_route_invalid_request(client):
    """test error handling in pkcro route"""

    response = client.post(url_for('auth.login_webauthn_pkcro_route'), status='*')
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_login_webauthn_invalid_assertion(client, webauthn_credential):
    """test login by webauthn; error hanling"""

    form_data = [('username', webauthn_credential.user.username), ('csrf_token', get_csrf_token(client))]
    response = client.post(url_for('auth.login_route'), params=form_data)
    assert response.status_code == HTTPStatus.OK
    assert response.json["webauthn_login"]

    form_data = [('assertion', 'invalid'), ('csrf_token', get_csrf_token(client))]
    response = client.post(url_for('auth.login_webauthn_route'), params=form_data, expect_errors=True)

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json["error"]["message"] == "Error during Webauthn authentication."


def test_login_oidc_route(client, user):
    """test_login_oidc_route"""

    authorize_redirect_mock = Mock(return_value=redirect('fake_redir_to_idp'))
    authorize_access_token_mock = Mock(return_value={'userinfo': {'email': user.email}})

    patch_oauth_redirect = patch.object(oauth.OIDC_DEFAULT, 'authorize_redirect', authorize_redirect_mock)
    patch_oauth_token = patch.object(oauth.OIDC_DEFAULT, 'authorize_access_token', authorize_access_token_mock)
    with patch_oauth_redirect, patch_oauth_token:
        response = client.get(url_for('auth.login_oidc_route'), expect_errors=True)
        assert response.status_code == HTTPStatus.FOUND
        assert response.headers['Location'] == 'fake_redir_to_idp'

        response = client.get(url_for('auth.login_oidc_callback_route'))
        assert response.status_code == HTTPStatus.OK

    authorize_redirect_mock.assert_called_once()
    authorize_access_token_mock.assert_called_once()


def test_login_oidc_route_noexist_user(client):
    """test non-existing user"""

    authorize_access_token_mock = Mock(return_value={'userinfo': {'email': 'notexist'}})

    patch_oauth_token = patch.object(oauth.OIDC_DEFAULT, 'authorize_access_token', authorize_access_token_mock)
    with patch_oauth_token:
        response = client.get(url_for('auth.login_oidc_callback_route'), expect_errors=True)
        assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert response.json['error']['message'] == 'OIDC authentication error.'

    authorize_access_token_mock.assert_called_once()


def test_login_oidc_route_disabled_oidc(client):
    """test disabled oidc redirects"""

    current_app.config['OIDC_NAME'] = None

    response = client.get(url_for('auth.login_oidc_route'), expect_errors=True)
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json['error']['message'] == 'OIDC is not enabled.'

    response = client.get(url_for('auth.login_oidc_callback_route'), expect_errors=True)
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json['error']['message'] == 'OIDC is not enabled.'


def test_login_oidc_route_handle_oidc_errors(client):
    """test_login_oidc_route"""

    authorize_redirect_mock = Mock(side_effect=AuthlibBaseError)
    authorize_access_token_mock = Mock(side_effect=AuthlibBaseError)

    patch_oauth_redirect = patch.object(oauth.OIDC_DEFAULT, 'authorize_redirect', authorize_redirect_mock)
    patch_oauth_token = patch.object(oauth.OIDC_DEFAULT, 'authorize_access_token', authorize_access_token_mock)

    with patch_oauth_redirect, patch_oauth_token:
        response = client.get(url_for('auth.login_oidc_route'), expect_errors=True)
        assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert response.json['error']['message'] == 'OIDC authentication error.'

        response = client.get(url_for('auth.login_oidc_callback_route'), expect_errors=True)
        assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert response.json['error']['message'] == 'OIDC authentication error.'

    authorize_redirect_mock.assert_called_once()
    authorize_access_token_mock.assert_called_once()
