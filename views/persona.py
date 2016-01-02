from flask import request, session, g, redirect, url_for, \
     render_template, flash, Blueprint, json
import requests
from bikeandwalk import app
import logging

mod = Blueprint('persona',__name__)

## persona authentication ##
@mod.route('/_auth/login', methods=['GET', 'POST'])
def login_handler():
    """This is used by the persona.js file to kick off the
    verification securely from the server side.  If all is okay
    the email address is remembered on the server.
    """
    resp = requests.post(app.config['PERSONA_VERIFIER'], data={
        'assertion': request.form['assertion'],
        'audience': request.host_url,
    }, verify=True)
    if resp.ok:
        verification_data = json.loads(resp.content)
        if verification_data['status'] == 'okay':
            session['email'] = verification_data['email']
            logging.info(verification_data['email'])
            return 'OK'

    abort(400)

@mod.route('/_auth/logout', methods=['POST'])
def logout_handler():
    """This is what persona.js will call to sign the user
    out again.
    """
    session.clear()
    return 'OK'
