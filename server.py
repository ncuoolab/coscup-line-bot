# -*- coding: utf-8 -*-

from flask import Flask, request
import coscupbot
import logging
import os
import sys

app = Flask(__name__)

credentials = {
    'channel_id': os.getenv("CHANNEL_ID"),
    'channel_secret': os.getenv("CHANNEL_SECRET"),
    'channel_mid': os.getenv("CHANNEL_MID"),
}

bot = None


@app.route('/')
def hello_world():
    return 'Hello, Coscup bot.'


@app.route('/callback', methods=['POST'])
def line_call_back():
    bot.process_new_event(request.get_data().decode("utf-8"))
    return "OK"


def init_logger():
    """
    Init logger. Default use INFO level. If 'DEBUG' is '1' in env use DEBUG level.
    :return:
    """
    root = logging.getLogger()
    ch = logging.StreamHandler(sys.stdout)
    level = logging.INFO
    if os.getenv("DEBUG") == '1':
        level = logging.DEBUG
    root.setLevel(level)
    ch.setLevel(level)
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(filename)s: - %(funcName)s(): - %(lineno)d: - %(message)s')
    ch.setFormatter(formatter)
    root.addHandler(ch)

if __name__ == '__main__':
    init_logger()
    logging.info('Init bot use credentials. %s' % credentials)
    bot = coscupbot.CoscupBot(credentials)
    ip = os.getenv("IP")
    port = os.getenv("PORT")
    app.run(host=ip, port=port)
