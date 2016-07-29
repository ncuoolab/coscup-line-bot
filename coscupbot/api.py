# -*- coding: utf-8 -*-

from linebot.client import *
import logging
from coscupbot import utils


def check_result(result):
    if result.status_code is 200:
        return result
    raise ApiError('Api Error. %s' % result.content, result)


class LineApi(object):
    def __init__(self, credentials):
        self.client = LineBotClient(**credentials)
        self.logger = logging.getLogger('LineApi')

    def send_text(self, **args):
        self.logger.info("Bot api send message. %s" % args)
        return check_result(self.client.send_text(**args))

    def reply_text(self, receive, message):
        self.send_text(to_mid=receive['from_mid'], text=message)

    def broadcast_new_message(self, mids, message):
        # notice up to 150 mid in one message request
        mids_list = utils.chunks(mids, 100)
        for mids in mids_list:
            self.send_text(to_mid=mids, text=message)
        pass


class ApiError(Exception):
    def __init__(self, message, request_result):
        super(ApiError, self).__init__(message)
        self.request_result = request_result
