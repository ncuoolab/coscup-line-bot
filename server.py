# -*- coding: utf-8 -*-

from flask import Flask, request
from flask import Response
from functools import wraps

import coscupbot
import logging
import os
import sys
from linebot import client

app = Flask(__name__)

BOT_TYPE = os.getenv("BOT_TYPE")

credentials =\
{
    'TRIAL': 
    {
        'channel_id': os.getenv("CHANNEL_ID"),
        'channel_secret': os.getenv("CHANNEL_SECRET"),
        'channel_mid': os.getenv("CHANNEL_MID")
    },
    'BUSINESS':
    {
        'channel_secret': os.getenv("CHANNEL_SECRET"),
        'channel_token': os.getenv("CHANNEL_TOKEN")
    }
}.get(BOT_TYPE)

sheet_credentials = {
    'credential_path': os.getenv('SHEET_CREDENTIAL_PATH'),
    'name': os.getenv('SHEET_NAME')
}

bot = None

PRODUCTION = '0'

ADMIN_ID = None
ADMIN_PWD = None


def init_logger():
    """
    Init logger. Default use INFO level. If 'DEBUG' is '1' in env use DEBUG level.
    :return:
    """
    root = logging.getLogger()
    ch = logging.StreamHandler(sys.stdout)
    fh = logging.FileHandler('coscupbot.log')
    level = logging.INFO
    if os.getenv("DEBUG") == '1':
        level = logging.DEBUG
    root.setLevel(level)
    ch.setLevel(level)
    fh.setLevel(level)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s: - %(funcName)s(): - %(lineno)d: - %(message)s')
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)
    root.addHandler(ch)
    root.addHandler(fh)


def get_wit_tokens():
    ret = {}
    if 'WIT_ZHTW_TOKEN' in os.environ:
        ret['zh-TW'] = os.environ['WIT_ZHTW_TOKEN']
    return ret


def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == ADMIN_ID and password == ADMIN_PWD


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)

    return decorated


init_logger()
logging.info('Init bot use credentials. %s' % credentials)
logging.info('Init bot use sheet credentials. %s' % sheet_credentials)
redis_url = os.getenv('REDIS', 'redis://localhost:6379')
bot = coscupbot.CoscupBot(BOT_TYPE, credentials, sheet_credentials, get_wit_tokens(), redis_url)
ip = os.getenv("IP")
port = os.getenv("PORT")
PRODUCTION = os.getenv('PRODUCTION', 0)
ADMIN_ID = os.environ['ADMIN_ID']
ADMIN_PWD = os.environ['ADMIN_PWD']


def create_new_app():
    app = Flask(__name__)
    return app


app = create_new_app()


@app.route('/')
def hello_world():
    return 'Hello, Coscup bot.'


@app.route('/callback', methods=['POST'])
def line_call_back():
    if PRODUCTION == '1':
        if not bot.bot_api.client.validate_signature(request.headers.get('X-Line-Channelsignature'),
                                                     request.get_data().decode("utf-8")):
            return "NOT PASS"
    bot.process_new_event(request.get_data().decode("utf-8"))
    return "OK"


@app.route('/edison')
def edison():
    ret = bot.get_edison_request()
    if ret is None:
        ret = '{}'
    resp = Response(response=ret,
                    status=200,
                    mimetype="application/json")

    return resp


@app.route('/edisondone')
def edison_done():
    data = request.get_data().decode("utf-8")
    bot.take_photo_done(data)
    return 'OK'


@app.route('/syncbackend')
@requires_auth
def sync_backend():
    '''
    Reget all data from google sheet.
    :return:
    '''
    if bot.sync_backend_data():
        return 'OK'
    return 'FAIL'


if __name__ == '__main__':
    app.run()
