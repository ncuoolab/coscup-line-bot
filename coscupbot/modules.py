# -*- coding: utf-8 -*-
from wit import Wit

from coscupbot import api, db, sheet
from coscupbot.model import NLPActions, GoogleSheetName
from wit import wit
import datetime
import logging
import random


def random_get_result(responses):
    return random.choice(responses).decode("utf-8")


class CommandController(object):
    def __init__(self, bot_api, db_url,lang):
        self.bot_api = bot_api
        self.dao = db.Dao(db_url)
        self.lang = lang

    def process_receive(self, receive):
        # echo Example. Will be remove.
        command = receive['content']['text']
        try:
            resp = self.dao.get_command_responses(command, self.lang)
            self.bot_api.send_text(to_mid=receive['from_mid'], text=resp)
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
        try:
            message = receive['content']['text']
            logging.info('Wit process new message %s' % message)
            session_id = 'sesseion-%s-%s' % (receive['from_mid'], datetime.datetime.now().strftime("%Y-%m-%d%H:%M:%S"))
            result = self.client.run_actions(session_id, message, self.convert_text_receive(receive),
                                             action_confidence=0.3)
            if 'processed' not in result:
                logging.warning('Message [%s] not run in action.' % message)
                response = random_get_result(self.dao.get_nlp_response(NLPActions.Error, self.lang))
                self.bot_api.reply_text(receive, response)
        except wit.WitError as we:
            logging.warning('Wit Process error %s' % we)
            response = random_get_result(self.dao.get_nlp_response(NLPActions.Error, self.lang))
            self.bot_api.reply_text(receive, response)
        except Exception as ex:
            logging.exception(ex)

    def send_message(self, request, response):
        pass

    def send_welcome(self, request):
        return self.send_nlp_action_message(request, NLPActions.Welcome)

    def send_location(self, request):
        return self.send_nlp_action_message(request, NLPActions.Location)

    def send_event_time(self, request):
        return self.send_nlp_action_message(request, NLPActions.EventTime)

    def send_nlp_action_message(self, request, action):
        logging.info('Process %s action. %s' % (action, request))
        response = random_get_result(self.dao.get_nlp_response(action, self.lang))
        from_mid = request['context']['from_mid']
        logging.info('Send %s message to %s, %s' % (action, from_mid, response))
        self.bot_api.send_text(to_mid=from_mid, text=response)
        return {'processed': True}

    def convert_text_receive(self, receive):
        return {'from_mid': receive['from_mid'], 'text': receive['content']['text']}


class SheetMessageController(object):
    def __init__(self, db_url, credential_path, spreadsheet_name, bot):
        self.dao = db.Dao(db_url)
        self.sheet = sheet.Sheet(credential_path, spreadsheet_name)
        self.bot = bot

    def parse_data_from_google_sheet(self):
        re = self.sheet.parse_all_data()
        self.dao.update_commands(re[GoogleSheetName.Command])
        self.dao.update_NLP_command(re[GoogleSheetName.NLPAction])
        for time_command in re[GoogleSheetName.Time]:
            self.bot.add_scheduler_message(*time_command)
        for realtime_command in re[GoogleSheetName.Realtime]:
            self.bot.realtime_msg_queue.put(realtime_command)
