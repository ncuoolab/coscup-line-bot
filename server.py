# -*- coding: utf-8 -*-

from flask import Flask, request
from flask import Response

import coscupbot
import logging
import os
import sys
from linebot import client

app = Flask(__name__)

credentials = {
    'channel_id': os.getenv("CHANNEL_ID"),
    'channel_secret': os.getenv("CHANNEL_SECRET"),
    'channel_mid': os.getenv("CHANNEL_MID"),
}

bot = None

PRODUCTION = '0'


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
        '%(asctime)s - %(levelname)s - %(filename)s: - %(funcName)s(): - %(lineno)d: - %(message)s')
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)
    root.addHandler(ch)
    root.addHandler(fh)


def get_wit_tokens():
    ret = {}
    if 'WIT_ZHTW_TOKEN' in os.environ:
        ret['zh_TW'] = os.environ['WIT_ZHTW_TOKEN']
    return ret


init_logger()
logging.info('Init bot use credentials. %s' % credentials)
redis_url = os.getenv('REDIS', 'redis://localhost:6379')
bot = coscupbot.CoscupBot(credentials, get_wit_tokens(), redis_url)
ip = os.getenv("IP")
port = os.getenv("PORT")
PRODUCTION = os.getenv('PRODUCTION', 0)


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
        if not client.validate_signature(request.headers.get('X-Line-Channelsignature'), request.get_data()):
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

if __name__ == '__main__':
    app.run()
