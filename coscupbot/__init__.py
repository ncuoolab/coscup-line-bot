# -*- coding: utf-8 -*-

from linebot.client import *
from linebot.receives import Receive
from coscupbot import api, db, modules
import logging
from concurrent.futures import ThreadPoolExecutor


class CoscupBot(object):
    def __init__(self, credentials, wit_tokens, db_url='redis://localhost:6379', num_thread=4):
        self.bot_api = api.LineApi(credentials)
        self.logger = logging.getLogger('CoscupBot')
        self.task_pool = ThreadPoolExecutor(num_thread)
        self.db_url = db_url
        self.message_controllers = self.gen_message_controllers(wit_tokens)

    def process_new_event(self, data):
        self.logger.debug('Process new receives. %s' % data)
        receive = Receive(data)
        for r in receive:
            content = r['content']
            self.logger.info('Get new %s message. %s' % (content, r))
            if isinstance(content, messages.TextMessage):
                # Handle text message
                self.task_pool.submit(self.handle_text_message, r)
            elif isinstance(content, messages.AudioMessage):
                # Handle audio message
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
        try:
            lang = self.check_fromuser_language(receive['from_mid'])
            self.message_controllers[lang].process_receive(receive)
        except Exception as ex:
            self.logger.error(ex)
        pass

    def check_fromuser_language(self, mid):
        return 'zh_TW'

    def gen_message_controllers(self, wittokens):
        ret = {}
        for key, value in wittokens.items():
            ret[key] = modules.WitMessageController(self.bot_api, wittokens[key], self.db_url,
                                                      key)
        return ret
