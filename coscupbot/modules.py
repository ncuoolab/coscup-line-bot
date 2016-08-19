# -*- coding: utf-8 -*-
import datetime
import logging
import random
from random import randint
from time import sleep
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
    def __init__(self, bot, db_url, lang):
        self.bot = bot
        self.bot_api = bot.bot_api
        self.dao = db.Dao(db_url)
        self.lang = lang
        self.action_commands = {
            '/login': self.boot_action,
            '/start': self.boot_action,
            '/boot': self.boot_action,
        }

        self.language_pack = {
            '中文': model.LanguageCode.zh_tw,
            'zh-TW': model.LanguageCode.zh_tw,
            'zh-tw': model.LanguageCode.zh_tw,
            'zh': model.LanguageCode.zh_tw,
            'TW': model.LanguageCode.zh_tw,
            'tw': model.LanguageCode.zh_tw,
            'Chinese': model.LanguageCode.zh_tw,
            'chinese': model.LanguageCode.zh_tw,
            'CHINESE': model.LanguageCode.zh_tw,
            'mandarin': model.LanguageCode.zh_tw,
            'Mandarin': model.LanguageCode.zh_tw,

            '英文': model.LanguageCode.en_us,
            'English': model.LanguageCode.en_us,
            'ENGLISH': model.LanguageCode.en_us,
            'english': model.LanguageCode.en_us,
            'en': model.LanguageCode.en_us,
            'en-US': model.LanguageCode.en_us,
            'en-us': model.LanguageCode.en_us,
            'EN': model.LanguageCode.en_us,
        }

        self.bool_pack = {
            '好': True,
            '好啊': True,
            '可以': True,
            '可': True,
            'Yes': True,
            'YES': True,
            'yes': True,
            'Y': True,
            'y': True,
            '不': False,
            '不用': False,
            'No': False,
            'NO': False,
            'no': False,
            'N': False,
            'n': False,
        }

    def process_receive(self, receive, humour=False):
        # echo Example. Will be remove.
        command = receive['content']['text']
        try:
            if command in self.action_commands:
                self.action_commands[command](receive, humour)
                return
            self.send_command_message(command, humour, receive)
        except Exception as ex:
            self.send_command_message('/commanderror', humour, receive)
            logging.error(ex)

    def send_command_message(self, command, humour, receive):
        resp = random_get_result(self.dao.get_command_responses(command, self.lang, humour))
        command_resp = model.CommandResponse.de_json(resp)
        for ns in command_resp.nonsense_responses:
            self.bot_api.send_text(to_mid=receive['from_mid'], text=ns)
            sleep(randint(1, 3))
        self.bot_api.send_text(to_mid=receive['from_mid'], text=command_resp.response_msg)

    def has_command(self, receive, humour=False):
        command = receive['content']['text']
        try:
            self.dao.get_command_responses(command, self.lang, humour)
        except Exception as ex:
            return False
        return True

    def boot_action(self, receive, humour=False):
        mid = receive['from_mid']
        logging.info('Trigger boot action from %s' % mid)
        self.bot.setup_next_step(mid, self.lang, self.set_language, 'COMMAND')
        self.send_command_message('/login', humour, receive)

    def set_language(self, receive, humour=False):
        mid = receive['from_mid']
        logging.info('Trigger set language action from %s' % mid)
        msg = receive['content']['text']
        if msg not in self.language_pack:
            self.send_command_message('/langerror', humour, receive)
            self.bot.setup_next_step(mid, self.lang, self.set_language, 'COMMAND')
        else:
            self.dao.set_mid_lang(mid, self.language_pack[msg])
            self.bot.setup_next_step(mid, self.lang, self.set_humour, 'COMMAND')
            self.send_command_message('/sethumour', humour, receive)

    def set_humour(self, receive, humour=False):
        mid = receive['from_mid']
        logging.info('Trigger set humour action from %s' % mid)
        msg = receive['content']['text']
        if msg not in self.bool_pack:
            self.send_command_message('/humourerror', humour, receive)
            self.bot.setup_next_step(mid, self.lang, self.set_humour, 'COMMAND')
        else:
            self.dao.set_mid_humour(mid, self.bool_pack[msg])
            self.send_command_message('/sethumourdone', humour, receive)


class WitMessageController(object):
    def __init__(self, bot, token, db_url, lang):
        self.token = token
        self.bot_api = bot.bot_api
        self.db_url = db_url
        self.lang = lang
        self.client = self.init_wit_client()
        self.dao = db.Dao(db_url)
        self.bot = bot
        self.logger = logging.getLogger('WitMessageController')

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
            'ShowSponsors': self.show_sponsors,
            'ShowSponsorIntro': self.show_sponsor_intro,
            'ShowBooths': self.show_booths,
            'ShowBoothIntro': self.show_booth_intro,
            'ShowDirty' : self.send_dirty,
            'ShowPokemon':self.send_pokemon,
            'ShowNothankyou':self.send_no_thankyou,
        }
        return Wit(access_token=self.token, actions=actions)

    def process_receive(self, receive):
        mid = receive['from_mid']
        try:
            message = receive['content']['text']
            self.logger.info('Wit process new message %s' % message)
            session_id = self.get_session_id(mid)
            result = self.client.run_actions(session_id, message, self.get_session_context(mid, receive),
                                             action_confidence=0.3)

            # if 'stop' in result:
            # Action done. Clear cache data.
            # self.clear_session_id(mid)

            if 'processed' not in result:
                self.logger.warning('Message [%s] not run in action.' % message)
                self.clear_session_id(mid)
                response = random_get_result(self.dao.get_nlp_response(NLPActions.Error, self.lang))
                self.bot_api.reply_text(receive, response)
        except wit.WitError as we:
            self.logger.warning('Wit Process error %s' % we)
            self.clear_session(mid)
            response = random_get_result(self.dao.get_nlp_response(NLPActions.Error, self.lang))
            self.bot_api.reply_text(receive, response)
        except Exception as ex:
            self.logger.exception(ex)
            self.clear_session(mid)
            response = random_get_result(self.dao.get_nlp_response(NLPActions.Error, self.lang))
            self.bot_api.reply_text(receive, response)

    def clear_session(self, mid):
        self.logger.info('Clear session for %s' % mid)
        self.clear_session_id(mid)
        self.clear_session_context(mid)

    def clear_session_by_request(self, request):
        mid = request['context']['from_mid']
        self.clear_session(mid)

    def get_session_id(self, mid):
        action = self.dao.get_session(mid)
        if action:
            return action
        session_id = 'sesseion-%s-%s' % (mid, datetime.datetime.now().strftime("%Y-%m-%d%H:%M:%S"))
        self.dao.add_session(mid, session_id)
        return session_id

    def clear_session_id(self, mid):
        self.dao.del_session(mid)

    def get_session_context(self, mid, receive):
        context = self.dao.get_context(mid)
        if context:
            context.pop('processed', None)
            self.dao.add_context(mid, context)
            return context
        context = self.convert_text_receive(receive)
        self.dao.add_context(mid, context)
        return context

    def clear_session_context(self, mid):
        self.dao.del_context(mid)

    def send_message(self, request, response):
        mid = request['context']['from_mid']
        msg = utils.to_utf8_str(response['text'])
        logging.info('Wit send message [%s] to [%s]', mid, msg)
        self.bot_api.send_text(to_mid=mid, text=msg)

    def send_pokemon(self, request):
        self.clear_session_by_request(request)
        return self.send_nlp_action_message(request, NLPActions.Pokemon)

    def send_no_thankyou(self, request):
        self.clear_session_by_request(request)
        return self.send_nlp_action_message(request, NLPActions.No_thankyou)

    def send_dirty(self, request):
        self.clear_session_by_request(request)
        return self.send_nlp_action_message(request, NLPActions.Dirty)

    def send_welcome(self, request):
        self.clear_session_by_request(request)
        return self.send_nlp_action_message(request, NLPActions.Welcome)

    def send_location(self, request):
        self.clear_session_by_request(request)
        return self.send_nlp_action_message(request, NLPActions.Location)

    def send_event_time(self, request):
        self.clear_session_by_request(request)
        return self.send_nlp_action_message(request, NLPActions.EventTime)

    def find_program_with_room(self, request):
        ctx = request['context']
        self.clear_session_by_request(request)
        try:
            if utils.get_wit_datetime_count(request) != 1:
                # If time not be only one. can not find program. response suggestioon.
                return self.send_nlp_action_message(request, NLPActions.Program_suggest)
            else:
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
        self.clear_session_by_request(request)
        return self.__set_response_message(ctx, resp)

    def get_program_help(self, request):
        cxt = request['context']
        response = random_get_result(self.dao.get_nlp_response(NLPActions.Program_help, self.lang))
        self.clear_session_by_request(request)
        return self.__set_response_message(cxt, response)

    def show_sponsors(self, request):
        cxt = request['context']
        response = self.bot.coscup_api_helper.show_sponsors(self.lang)
        return self.__set_response_message(cxt, response)

    def show_sponsor_intro(self, request):
        cxt = request['context']
        sp_name = utils.get_wit_sponsor_name(request)
        response = self.bot.coscup_api_helper.show_sponsor_intro(sp_name, self.lang)
        self.clear_session_by_request(request)
        return self.__set_response_message(cxt, response)

    def show_booths(self, request):
        cxt = request['context']
        response = self.bot.coscup_api_helper.show_booths(self.lang)
        # self.bot.setup_next_step(cxt['from_mid'], self.lang, self.show_booth_intro)
        return self.__set_response_message(cxt, response, 'booths_response_msg')

    def show_booth_intro(self, request):
        cxt = request['context']
        booth_name = utils.get_wit_booth(request)
        response = self.bot.coscup_api_helper.show_booth_intro(booth_name, self.lang)
        self.clear_session_by_request(request)
        return self.__set_response_message(cxt, response, 'boothintro_response_msg')

    def send_nlp_action_message(self, request, action):
        logging.info('Process %s action. %s' % (action, request))
        response = random_get_result(self.dao.get_nlp_response(action, self.lang))
        ctx = request['context']
        return self.__set_response_message(ctx, response)

    def __set_response_message(self, context, message, responsekey='response_msg'):
        context[responsekey] = message
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
        self.booths = None
        self.load_db_to_cache()

    def find_program_by_room_time(self, room, time, lang):
        program = self.__find_program_by_room_time(room, time)
        if program:
            return self.__gen_template_result(NLPActions.Program_result, lang, program=program, time=time)
        program = self.__find_program_by_room_near(room, time)
        if program:
            return self.__gen_template_result(NLPActions.Program_near, lang, program=program, time=time)
        return random_get_result(self.dao.get_nlp_response(NLPActions.Program_not_found, lang))

    def __find_program_by_room_time(self, room, time):
        for program in self.programs:
            if program.room == room and program.starttime <= time < program.endtime:
                return program
        return None

    def __find_program_by_room_near(self, room, time):
        time = time + datetime.timedelta(minutes=20)
        return self.__find_program_by_room_time(room, time)

    def show_transport_types(self, lang):
        transport_types = self.transport.get_transport_types(lang)
        return self.__gen_template_result(NLPActions.Show_transport_types, lang, transport_types=transport_types)

    def show_transport_result(self, trans_type, lang):
        logging.info('Get transport result.[Type] %s, [Labg] %s', trans_type, lang)
        return self.transport.get_transport_result(trans_type, lang)

    def show_sponsors(self, lang):
        return self.__gen_template_result(NLPActions.Show_sponsors, lang, sponsors=self.sponsors)

    def show_booths(self, lang):
        return self.__gen_template_result(NLPActions.Show_booths, lang, booths=self.booths)

    def show_sponsor_intro(self, sponsor_name, lang):
        for sp in self.sponsors:
            if sponsor_name == sp.name_en or sponsor_name == sp.name_zh:
                return self.__gen_template_result(NLPActions.Sponsor_intro, lang, sponsor=sp)
        raise Exception('Search Sponsor error. %s not found.' % sponsor_name)

    def show_booth_intro(self, booth_name, lang):
        for booth in self.booths:
            if booth_name.upper() == booth.booth.upper():
                return self.__gen_template_result(NLPActions.Booth_Intro, lang, booth=booth)
        raise Exception('Search booth error. %s not found.' % booth_name)

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
        self.get_booth_to_db()
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

    def get_booth_to_db(self):
        url = self.backend_url + '/booth.json'
        logging.info('Start to get booth data from coscup api. %s', url)
        response = self.__get_url_content(url)
        logging.debug('Get booth from coscup api. %s', response)
        self.dao.save_coscup_api_data(CoscupApiType.booth, response)

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
            self.booths = model.Booth.de_json_list(self.dao.get_coscup_api_data(CoscupApiType.booth))
        except Exception as ex:
            logging.exception(ex)
