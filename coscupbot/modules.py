# -*- coding: utf-8 -*-
import datetime
import logging
import random
from urllib.request import urlopen

from mako.template import Template
from wit import Wit
from wit import wit

from coscupbot import db, sheet, utils, model
from coscupbot.model import NLPActions, GoogleSheetName, CoscupApiType

COSCUP_BACKEND_URL = 'http://coscup.org/2016-assets/json'


def random_get_result(responses):
    return random.choice(responses).decode("utf-8")


class CommandController(object):
    def __init__(self, bot_api, db_url, lang):
        self.bot_api = bot_api
        self.dao = db.Dao(db_url)
        self.lang = lang

    def process_receive(self, receive):
        # echo Example. Will be remove.
        command = receive['content']['text']
        try:
            resp = random_get_result(self.dao.get_command_responses(command, self.lang))
            self.bot_api.send_text(to_mid=receive['from_mid'], text=resp)
        except Exception as ex:
            logging.error(ex)


class WitMessageController(object):
    def __init__(self, bot, token, db_url, lang):
        self.token = token
        self.bot_api = bot.bot_api
        self.db_url = db_url
        self.lang = lang
        self.client = self.init_wit_client()
        self.dao = db.Dao(db_url)
        self.mid_action = {}
        self.action_context = {}
        self.bot = bot

    def init_wit_client(self):
        actions = {
            'send': self.send_message,
            'Welcome': self.send_welcome,
            'GetLocation': self.send_location,
            'GetEventTime': self.send_event_time,
            'GetProgramHelp': self.get_program_help,
            'FindProgramWithRoom': self.find_program_with_room,
            'ShowTransportType': self.show_transport_types,
            'ShowTransport': self.show_transport_result,
        }
        return Wit(access_token=self.token, actions=actions)

    def process_receive(self, receive):
        mid = receive['from_mid']
        try:
            message = receive['content']['text']
            logging.info('Wit process new message %s' % message)
            session_id = self.get_session_id(mid)
            result = self.client.run_actions(session_id, message, self.get_session_context(mid, receive),
                                             action_confidence=0.3)

            if 'stop' in result:
                # Action done. Clear cache data.
                self.clear_session_id(mid)

            if 'processed' not in result:
                logging.warning('Message [%s] not run in action.' % message)
                self.clear_session_id(mid)
                response = random_get_result(self.dao.get_nlp_response(NLPActions.Error, self.lang))
                self.bot_api.reply_text(receive, response)
        except wit.WitError as we:
            logging.warning('Wit Process error %s' % we)
            self.clear_session(mid)
            response = random_get_result(self.dao.get_nlp_response(NLPActions.Error, self.lang))
            self.bot_api.reply_text(receive, response)
        except Exception as ex:
            logging.exception(ex)
            self.clear_session(mid)
            response = random_get_result(self.dao.get_nlp_response(NLPActions.Error, self.lang))
            self.bot_api.reply_text(receive, response)

    def clear_session(self, mid):
        self.clear_session_id(mid)
        self.clear_session_context(mid)

    def get_session_id(self, mid):
        if mid in self.mid_action:
            return self.mid_action[mid]
        session_id = 'sesseion-%s-%s' % (mid, datetime.datetime.now().strftime("%Y-%m-%d%H:%M:%S"))
        self.mid_action[mid] = session_id
        return session_id

    def clear_session_id(self, mid):
        self.mid_action.pop(mid, None)

    def get_session_context(self, mid, receive):
        if mid in self.action_context:
            self.action_context[mid].pop('processed', None)
            return self.action_context[mid]
        self.action_context[mid] = self.convert_text_receive(receive)
        return self.action_context[mid]

    def clear_session_context(self, mid):
        self.action_context.pop(mid, None)

    def send_message(self, request, response):
        mid = request['context']['from_mid']
        msg = utils.to_utf8_str(response['text'])
        logging.info('Wit send message [%s] to [%s]', mid, msg)
        self.bot_api.send_text(to_mid=mid, text=msg)

    def send_welcome(self, request):
        return self.send_nlp_action_message(request, NLPActions.Welcome)

    def send_location(self, request):
        return self.send_nlp_action_message(request, NLPActions.Location)

    def send_event_time(self, request):
        return self.send_nlp_action_message(request, NLPActions.EventTime)

    def find_program_with_room(self, request):
        ctx = request['context']
        try:
            time = utils.get_wit_datetimes(request)
            room = utils.get_wit_room(request)
            resp = self.bot.coscup_api_helper.find_program_by_room_time(room, time, self.lang)
            ctx = self.__set_response_message(ctx, resp)
        except Exception as ex:
            logging.exception(ex)

        return ctx

    def show_transport_types(self, request):
        ctx = request['context']
        resp = self.bot.coscup_api_helper.show_transport_types(self.lang)
        return self.__set_response_message(ctx, resp)

    def show_transport_result(self, request):
        ctx = request['context']
        transport = utils.get_wit_transport_type(request)
        resp = self.bot.coscup_api_helper.show_transport_result(transport, self.lang)
        return self.__set_response_message(ctx, resp)

    def get_program_help(self, request):
        logging.info('Process %s action. %s' % (NLPActions.Program_help, request))
        cxt = request['context']
        response = random_get_result(self.dao.get_nlp_response(NLPActions.Program_help, self.lang))
        return self.__set_response_message(cxt, response)

    def send_nlp_action_message(self, request, action):
        logging.info('Process %s action. %s' % (action, request))
        response = random_get_result(self.dao.get_nlp_response(action, self.lang))
        ctx = request['context']
        return self.__set_response_message(ctx, response)

    def __set_response_message(self, context, message):
        context['response_msg'] = message
        context['processed'] = True
        return context

    def convert_text_receive(self, receive):
        return {'from_mid': receive['from_mid'], 'text': receive['content']['text']}


class SheetMessageController(object):
    def __init__(self, db_url, credential_path, spreadsheet_name, bot):
        self.dao = db.Dao(db_url)
        self.bot = bot
        self.credential_path = credential_path
        self.spreadsheet_name = spreadsheet_name

    def parse_data_from_google_sheet(self):
        re = self.__create_sheet().parse_all_data()
        self.dao.update_commands(re[GoogleSheetName.Command])
        self.dao.update_NLP_command(re[GoogleSheetName.NLPAction])
        for time_command in re[GoogleSheetName.Time]:
            self.bot.add_scheduler_message(*time_command)
        for realtime_command in re[GoogleSheetName.Realtime]:
            self.bot.realtime_msg_queue.put(realtime_command)

    def __create_sheet(self):
        return sheet.Sheet(self.credential_path, self.spreadsheet_name)


class CoscupInfoHelper(object):
    def __init__(self, db_url, backend_url=COSCUP_BACKEND_URL):
        self.backend_url = backend_url
        self.dao = db.Dao(db_url)
        self.programs = None
        self.rooms = None
        self.program_type = None
        self.sponsors = None
        self.levels = None
        self.transport = None
        self.staffs = None
        self.load_db_to_cache()

    def find_program_by_room_time(self, room, time, lang):
        program = self.__find_program_by_room_time(room, time)
        if program is None:
            return random_get_result(self.dao.get_nlp_response(NLPActions.Program_not_found, lang))
        return self.__gen_template_result(NLPActions.Program_result, lang, program=program, time=time)

    def __find_program_by_room_time(self, room, time):
        for program in self.programs:
            if program.room == room and program.starttime < time < program.endtime:
                return program
        return None

    def show_transport_types(self, lang):
        transport_types = self.transport.get_transport_types(lang)
        return self.__gen_template_result(NLPActions.Show_transport_types, lang, transport_types=transport_types)

    def show_transport_result(self, trans_type, lang):
        return self.transport.get_transport_result(trans_type, lang)

    def __gen_template_result(self, nlp_action, lang, **args):
        tem_str = random_get_result(self.dao.get_nlp_response(nlp_action, lang))
        t = Template(tem_str)
        return t.render(**args)

    def sync_backend(self):
        self.get_program_to_db()
        self.get_room_to_db()
        self.get_type_to_db()
        self.get_sponsor_to_db()
        self.get_level_to_db()
        self.get_transport_to_db()
        self.get_staff_to_db()
        self.load_db_to_cache()

    def get_program_to_db(self):
        url = self.backend_url + '/program.json'
        logging.info('Start to get program data from coscup api. %s', url)
        response = self.__get_url_content(url)
        logging.debug('Get program data from coscup api. %s', response)
        self.dao.save_coscup_api_data(CoscupApiType.program, response)

    def get_room_to_db(self):
        url = self.backend_url + '/room.json'
        logging.info('Start to get room data from coscup api. %s', url)
        response = self.__get_url_content(url)
        logging.debug('Get program room from coscup api. %s', response)
        self.dao.save_coscup_api_data(CoscupApiType.room, response)

    def get_type_to_db(self):
        url = self.backend_url + '/type.json'
        logging.info('Start to get type data from coscup api. %s', url)
        response = self.__get_url_content(url)
        logging.debug('Get program type from coscup api. %s', response)
        self.dao.save_coscup_api_data(CoscupApiType.program_type, response)

    def get_sponsor_to_db(self):
        url = self.backend_url + '/sponsor.json'
        logging.info('Start to get sponsor data from coscup api. %s', url)
        response = self.__get_url_content(url)
        logging.debug('Get program sponsor from coscup api. %s', response)
        self.dao.save_coscup_api_data(CoscupApiType.sponsor, response)

    def get_level_to_db(self):
        url = self.backend_url + '/level.json'
        logging.info('Start to get level data from coscup api. %s', url)
        response = self.__get_url_content(url)
        logging.debug('Get program level from coscup api. %s', response)
        self.dao.save_coscup_api_data(CoscupApiType.level, response)

    def get_transport_to_db(self):
        url = self.backend_url + '/transport.json'
        logging.info('Start to get transport data from coscup api. %s', url)
        response = self.__get_url_content(url)
        logging.debug('Get program transport from coscup api. %s', response)
        self.dao.save_coscup_api_data(CoscupApiType.transport, response)

    def get_staff_to_db(self):
        url = self.backend_url + '/staff.json'
        logging.info('Start to get staff data from coscup api. %s', url)
        response = self.__get_url_content(url)
        logging.debug('Get program staff from coscup api. %s', response)
        self.dao.save_coscup_api_data(CoscupApiType.staff, response)

    def __get_url_content(self, url):
        with urlopen(url) as response:
            ret = response.read()
        return ret

    def load_db_to_cache(self):
        try:
            self.programs = model.Program.de_json_list(self.dao.get_coscup_api_data(CoscupApiType.program))
            self.rooms = model.Room.de_json_list(self.dao.get_coscup_api_data(CoscupApiType.room))
            self.program_type = model.ProgramType.de_json_list(self.dao.get_coscup_api_data(CoscupApiType.program_type))
            self.sponsors = model.Sponsor.de_json_list(self.dao.get_coscup_api_data(CoscupApiType.sponsor))
            self.levels = model.Level.de_json_list(self.dao.get_coscup_api_data(CoscupApiType.level))
            self.transport = model.Transport.de_json(self.dao.get_coscup_api_data(CoscupApiType.transport))
            self.staffs = model.Staff.de_json_list(self.dao.get_coscup_api_data(CoscupApiType.staff))
        except Exception as ex:
            logging.exception(ex)
