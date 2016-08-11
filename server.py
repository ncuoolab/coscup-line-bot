# -*- coding: utf-8 -*-

import logging
import logging.config
import os
from functools import wraps

from flask import Flask, request
from flask import Response, jsonify

import coscupbot

app = Flask(__name__)

BOT_TYPE = os.getenv("BOT_TYPE")

credentials = \
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
    logging.config.fileConfig("./logging.conf")
    root = logging.getLogger()
    level = logging.INFO
    if os.getenv("DEBUG") == '1':
        level = logging.DEBUG
    root.setLevel(level)


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
@requires_auth
def edison():
    ret_json = {}
    ret = bot.get_edison_request()
    if ret:
        ret_json['mid'] = ret
    return jsonify(ret_json)


@app.route('/edisondone', methods=['POST'])
@requires_auth
def edison_done():
    data = request.get_data().decode("utf-8")
    bot.take_photo_done(data)
    return 'OK'


@app.route('/triggerrealtime')
@requires_auth
def trigger_broadcast_realtime():
    result = bot.broadcast_realtime_message()
    return str(result)


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


@app.route('/groundstatus/<mid>')
@requires_auth
def get_gorund_status(mid):
    return jsonify(bot.get_ground_game_status(mid))


@app.route('/groundcheckin/<sp_id>/<mid>')
@requires_auth
def manual_check_in(sp_id, mid):
    return jsonify(bot.ground_game_check_in(sp_id, mid))

@app.route('/sp/')
def sp_index():
    return jsonify(statue=True, message="Welcome, traveller! >_O")

@app.route('/sp/<sp_id>')
def sp_with_id(sp_id):
    return render_template('index.html', sp_id=sp_id, sp_data=sp_dict[sp_id])

@app.route('/sp/<sp_id>/<mid>')
def sp_check_in(sp_id, mid):
    ret = manual_check_in(sp_id, mid)
    return render_template('check_in.html', ret)

if __name__ == '__main__':
    app.run()
