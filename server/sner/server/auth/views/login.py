# This file is part of sner4 project governed by MIT license, see the LICENSE.txt file.
"""
auth login/authentication views
"""

from base64 import b64decode, b64encode
from http import HTTPStatus

from authlib.common.errors import AuthlibBaseError
from fido2 import cbor
from fido2.webauthn import AuthenticatorData, CollectedClientData
from flask import current_app, Response, session, url_for, jsonify
from flask_login import login_user, logout_user
from requests.exceptions import HTTPError
from sqlalchemy import func

from sner.server.auth.core import regenerate_session, TOTPImpl, webauthn_credentials
from sner.server.auth.forms import LoginForm, TotpCodeForm, WebauthnLoginForm
from sner.server.auth.models import User
from sner.server.auth.views import blueprint
from sner.server.extensions import oauth, webauthn
from sner.server.forms import ButtonForm
from sner.server.password_supervisor import PasswordSupervisor as PWS
from sner.server.utils import error_response


@blueprint.route('/login', methods=['POST'])
def login_route():
    """login route"""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter(User.active, User.username == form.username.data).one_or_none()
        if user:
            if form.password.data:
                if PWS.compare(PWS.hash(form.password.data, PWS.get_salt(user.password)), user.password):
                    if user.totp:
                        session['totp_login_user_id'] = user.id
                        return jsonify({"totp_login_required": True})

                    regenerate_session()
                    login_user(user)
                    current_app.logger.info('auth.login password')

                    return jsonify({
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "roles": user.roles
                    })
            else:
                if user.webauthn_credentials:
                    session['webauthn_login_user_id'] = user.id
                    return jsonify({"webauthn_login": True})

    return error_response(message='Invalid credentials.', code=HTTPStatus.UNAUTHORIZED)


@blueprint.route('/logout')
def logout_route():
    """logout route"""

    current_app.logger.info('auth.logout')
    logout_user()
    session.clear()

    return jsonify({"message": "Successfully logged out."})


@blueprint.route('/login_totp', methods=['POST'])
def login_totp_route():
    """login totp route"""

    user = User.query.filter(User.active, User.id == session.get('totp_login_user_id')).one_or_none()
    if not user:
        return error_response(message='Unauthorized.', code=HTTPStatus.UNAUTHORIZED)

    form = TotpCodeForm()
    if form.validate_on_submit():
        if TOTPImpl(user.totp).verify_code(form.code.data):
            regenerate_session()
            login_user(user)
            current_app.logger.info('auth.login totp')
            return jsonify({
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "roles": user.roles
            })

        return error_response(message='Invalid code.', code=HTTPStatus.BAD_REQUEST)

    return error_response(message='Form is invalid.', errors=form.errors, code=HTTPStatus.BAD_REQUEST)


@blueprint.route('/login_webauthn_pkcro', methods=['POST'])
def login_webauthn_pkcro_route():
    """login webauthn pkcro route"""

    user = User.query.filter(User.active, User.id == session.get('webauthn_login_user_id')).one_or_none()
    form = ButtonForm()
    if user and form.validate_on_submit():
        pkcro, state = webauthn.authenticate_begin(webauthn_credentials(user))
        session['webauthn_login_state'] = state
        return Response(b64encode(cbor.encode(pkcro)).decode('utf-8'), mimetype='text/plain')

    return '', HTTPStatus.BAD_REQUEST


@blueprint.route('/login_webauthn', methods=['GET', 'POST'])
def login_webauthn_route():
    """login webauthn route"""

    user = User.query.filter(User.active, User.id == session.get('webauthn_login_user_id')).one_or_none()
    if not user:
        return error_response(message='Unauthorized.', code=HTTPStatus.UNAUTHORIZED)

    form = WebauthnLoginForm()
    if form.validate_on_submit():
        try:
            assertion = cbor.decode(b64decode(form.assertion.data))
            webauthn.authenticate_complete(
                session.pop('webauthn_login_state'),
                webauthn_credentials(user),
                assertion['credentialRawId'],
                CollectedClientData(assertion['clientDataJSON']),
                AuthenticatorData(assertion['authenticatorData']),
                assertion['signature'])
            regenerate_session()
            login_user(user)
            current_app.logger.info('auth.login webauthn')
            return jsonify({
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "roles": user.roles
            })

        except (KeyError, ValueError) as exc:
            current_app.logger.exception(exc)
            return error_response(message='Error during Webauthn authentication.', code=HTTPStatus.BAD_REQUEST)

    return error_response(message='Form is invalid.', errors=form.errors, code=HTTPStatus.BAD_REQUEST)


@blueprint.route('/login_oidc')
def login_oidc_route():
    """login oidc"""

    if not current_app.config['OIDC_NAME']:
        return jsonify({'error': {
            'code': HTTPStatus.BAD_REQUEST,
            'message': 'OIDC is not enabled.'
        }}), HTTPStatus.BAD_REQUEST

    redirect_uri = current_app.config.get(
        f'{current_app.config["OIDC_NAME"]}_REDIRECT_URI',
        url_for('auth.login_oidc_callback_route', _external=True)
    )
    try:
        return getattr(oauth, current_app.config['OIDC_NAME']).authorize_redirect(redirect_uri)
    except (HTTPError, AuthlibBaseError) as exc:
        current_app.logger.exception(exc)

    return error_response(message='OIDC authentication error.', code=HTTPStatus.INTERNAL_SERVER_ERROR)


@blueprint.route('/login_oidc_callback')
def login_oidc_callback_route():
    """login oidc callback"""

    if not current_app.config['OIDC_NAME']:
        return error_response(message='OIDC is not enabled.', code=HTTPStatus.BAD_REQUEST)

    try:
        token = getattr(oauth, current_app.config['OIDC_NAME']).authorize_access_token()
        userinfo = token.get('userinfo')
    except (HTTPError, AuthlibBaseError) as exc:
        current_app.logger.exception(exc)
        return error_response(message='OIDC authentication error.', code=HTTPStatus.INTERNAL_SERVER_ERROR)

    if userinfo and userinfo.get('email'):
        user = User.query.filter(User.active, func.lower(User.email) == userinfo.get('email').lower()).one_or_none()
        if user:
            regenerate_session()
            login_user(user)
            current_app.logger.info('auth.login oidc')
            return jsonify({
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "roles": user.roles
            })

    return error_response(message='OIDC authentication error.', code=HTTPStatus.INTERNAL_SERVER_ERROR)
