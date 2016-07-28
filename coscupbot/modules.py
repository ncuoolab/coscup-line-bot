# -*- coding: utf-8 -*-
from wit import Wit

from coscupbot import api, db
from coscupbot.model import NLPActions
import datetime
import logging
import random


def random_get_result(responses):
    return random.choice(responses).decode("utf-8")


class MessageController(object):
    def __init__(self, bot_api, db_url):
        self.bot_api = bot_api
        self.dao = db.Dao(db_url)

    def process_receive(self, receive):
        # echo Example. Will be remove.
        response_text = receive['content']['text']
        try:
            self.bot_api.send_text(to_mid=receive['from_mid'], text=response_text)
        except Exception as ex:
            self.logger.error(ex)


class WitMessageController(object):
    def __init__(self, bot_api, token, db_url, lang):
        self.token = token
        self.bot_api = bot_api
        self.db_url = db_url
        self.lang = lang
        self.client = self.init_wit_client()
        self.dao = db.Dao(db_url)

    def init_wit_client(self):
        actions = {
            'send': self.send_message,
            'Welcome': self.send_welcome,
            'GetLocation': self.send_location,
            'GetEventTime': self.send_event_time,
        }
        return Wit(access_token=self.token, actions=actions)

    def process_receive(self, receive):
        message = receive['content']['text']
        logging.info('Wit process new message %s' % message)
        session_id = 'sesseion-%s-%s' % (receive['from_mid'], datetime.datetime.now().strftime("%Y-%m-%d%H:%M:%S"))
        self.client.run_actions(session_id, message, self.convert_text_receive(receive), action_confidence=0.8)
        pass

    def send_message(self, request, response):
        pass

    def send_welcome(self, request):
        self.send_nlp_action_message(request, NLPActions.Welcome)
        pass

    def send_location(self, request):
        self.send_nlp_action_message(request, NLPActions.Location)
        pass

    def send_event_time(self, request):
        self.send_nlp_action_message(request, NLPActions.EventTime)
        pass

    def send_nlp_action_message(self, request, action):
        logging.info('Process %s action. %s' % (action, request))
        response = random_get_result(self.dao.get_nlp_response(action, self.lang))
        from_mid = request['context']['from_mid']
        logging.info('Send %s message to %s, %s' % (action, from_mid, response))
        self.bot_api.send_text(to_mid=from_mid, text=response)
        pass

    def convert_text_receive(self, receive):
        return {'from_mid': receive['from_mid'], 'text': receive['content']['text']}
