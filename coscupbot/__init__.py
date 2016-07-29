# -*- coding: utf-8 -*-

from linebot.client import *
from linebot.receives import Receive
from coscupbot import api, db, modules, utils
import logging
import redis
from concurrent.futures import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler


class CoscupBot(object):
    def __init__(self, credentials, wit_tokens, db_url='redis://localhost:6379', num_thread=4):
        self.bot_api = api.LineApi(credentials)
        self.logger = logging.getLogger('CoscupBot')
        self.task_pool = ThreadPoolExecutor(num_thread)
        self.db_url = db_url
        self.dao = db.Dao(db_url)
        self.nlp_message_controllers = self.gen_nlp_message_controllers(wit_tokens)
        self.command_message_controllers = self.gen_command_message_controllers(['zh_TW', 'en_US'])
        self.edison_queue = utils.RedisQueue('edison', 'queue',
                                             connection_pool=redis.ConnectionPool.from_url(url=db_url))
        self.job_scheduler = BackgroundScheduler()
        self.realtime_msg_queue = utils.RedisQueue('realmessage', 'queue',
                                                   connection_pool=redis.ConnectionPool.from_url(url=db_url))

        self.start_scheduler()

    def process_new_event(self, data):
        self.logger.debug('Process new receives. %s' % data)
        receive = Receive(data)
        for r in receive:
            content = r['content']
            self.logger.info('Get new %s message. %s' % (content, r))
            self.try_set_mid(r)
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

    def try_set_mid(self, receive):
        """
        try to save mid to database from receive.
        :param r:
        :return:
        """
        try:
            self.dao.add_user_mid(receive['from_mid'])
        except Exception as ex:
            self.logger.exception(ex)

    def handle_text_message(self, receive):
        try:
            lang = self.check_fromuser_language(receive['from_mid'])
            msg = receive['content']['text']
            if msg.startswith('/'):
                self.command_message_controllers[lang].process_receive(receive)
            else:
                self.nlp_message_controllers[lang].process_receive(receive)
        except Exception as ex:
            self.logger.error(ex)
        pass

    def check_fromuser_language(self, mid):
        return 'zh_TW'

    def gen_nlp_message_controllers(self, wittokens):
        ret = {}
        for key, value in wittokens.items():
            ret[key] = modules.WitMessageController(self.bot_api, wittokens[key], self.db_url,
                                                    key)
        return ret

    def gen_command_message_controllers(self, langs):
        ret = {}
        for lang in langs:
            ret[lang] = modules.CommandController(self.bot_api, self.db_url, lang)
        return ret

    def get_edison_request(self):
        self.edison_queue.get(timeout=10)

    def take_photo_done(self, data):
        # TODO
        pass

    def broadcast_realtime_message(self):
        """
        this method will take message from realtime_msg_queue. If no message in queue will pass.
        :return:
        """
        self.logger.info('Start Broadcast real time message.')
        while True:
            rmsg = self.realtime_msg_queue.get(block=False)
            if rmsg is None:
                self.logger.debug('No real time message now.')
                break
            msg = rmsg.decode('utf-8')
            mids = self.dao.get_all_user_mid()
            self.logger.info('Start broadcast real time message %s to %d mids.' % (rmsg, len(mids)))
            self.bot_api.broadcast_new_message(mids, msg)

    def start_scheduler(self):
        self.job_scheduler.add_job(self.broadcast_realtime_message, 'interval', seconds=5)
        self.job_scheduler.start()

    def reset_scheduler(self):
        self.job_scheduler.shutdown(wait=False)
        self.job_scheduler = BackgroundScheduler()
        self.start_scheduler()

