# -*- coding: utf-8 -*-

from linebot.client import *
from linebot.receives import Receive
from coscupbot import api, db
import logging


class CoscupBot(object):
    def __init__(self, credentials, db_url='redis://localhost:6379'):
        self.botapi = api.LineApi(credentials)
        self.logger = logging.getLogger('CoscupBot')
        self.dao = db.Dao(db_url)

    def process_new_event(self, data):
        self.logger.debug('Process new receives. %s' % data)
        receive = Receive(data)
        for r in receive:
            content = r['content']
            self.logger.info('Get new %s message. %s' % (content, r))
            if isinstance(content, messages.TextMessage):
                # Handle text message
                self.handle_text_message(r)
            elif isinstance(content, messages.AudioMessage):
                # Handle aduio message
                pass
            elif isinstance(content, messages.ImageMessage):
                # handle Image message
                pass
            elif isinstance(content, messages.LocationMessage):
                # handle Location message
                pass
            elif isinstance(content, messages.StickerMessage):
                # handle Sticker message
                pass
            elif isinstance(content, messages.VideoMessage):
                # handle Video message
                pass
            else:
                logging.error('Not support content %s. %s' % (content, r))

    def handle_text_message(self, receive):
        # echo Example. Will be remove.
        response_text = receive['content']['text']
        try:
            self.botapi.send_text(to_mid=receive['from_mid'], text=response_text)
        except Exception as ex:
            self.logger.error(ex)
