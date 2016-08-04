# -*- coding: utf-8 -*-
import datetime
import json

import pytz

tz = pytz.timezone('Asia/Taipei')


def check_json(json_type):
    """
    Checks whether json_type is a dict or a string. If it is already a dict, it is returned as-is.
    If it is not, it is converted to a dict by means of json.loads(json_type)
    :param json_type:
    :return:
    """
    str_types = (str,)

    if type(json_type) == dict:
        return json_type
    elif type(json_type) in str_types:
        return json.loads(json_type)
    else:
        raise ValueError("json_type should be a json dict or string.")


def try_parse_datetime(datetime_string):
    try:
        utc_dt = datetime.datetime.strptime(datetime_string, "%Y-%m-%dT%H:%M:%S.%fZ")
        local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(tz)
        return tz.normalize(local_dt)
    except Exception as ex:
        return None


class Command(object):
    def __init__(self, language, command_str, response):
        """
        Command object.
        :param language: language set. eg. zh_TW
        :param command_str: string to trigger command. eg. help
        :param response: list of response content. eg. ['hi', 'hello']
        """
        self.command_str = command_str
        self.language = language
        self.response = response


class NlpAction(object):
    def __init__(self, language, action_str, responses):
        """
        Command object.
        :param language: language set. eg. zh_TW
        :param command_str: string to trigger command. eg. help
        :param response: list of response content. eg. ['hi', 'hello']
        """
        self.action_str = action_str
        self.language = language
        self.response = responses


class NLPActions(object):
    Welcome = 'WELCOME'
    Location = 'LOCATION'
    EventTime = 'EVENTTIME'
    Error = 'ERROR'
    Program_help = 'PROGRAMHELP'
    Program_not_found = 'PROGRAMNOTFUND'
    Program_result = 'PROGRAMRESULT'
    Show_transport_types = 'SHOWTRANSPORTTYPES'
    Edison_request = 'EDISONREQUEST'
    Show_sponsors = 'SHOWSPONSORS'
    Sponsor_intro = 'SPONSORINTRO'


class GoogleSheetName(object):
    Command = 'COMMAND'
    NLPAction = 'NLP_ACTION'
    Realtime = 'REALTIME'
    Time = 'TIME'


class CoscupApiType(object):
    program = 'PROGRAM'
    room = 'ROOM'
    program_type = 'PROGRAMTYPE'
    sponsor = 'SPONSOR'
    level = 'LEVEL'
    transport = 'TRANSPORT'
    staff = 'STAFF'


class LanguageCode(object):
    zh_tw = 'zh-TW'
    en_us = 'en-US'


class Program(object):
    @classmethod
    def de_json_list(cls, json_string):
        jsonobj = check_json(json_string)
        ret = []
        for program_json in jsonobj:
            ret.append(Program.de_json(program_json))
        return ret

    @classmethod
    def de_json(cls, jsonobj):
        slot = jsonobj.get('slot')
        room = jsonobj.get('room')
        starttime = try_parse_datetime(jsonobj.get('starttime'))
        endtime = try_parse_datetime(jsonobj.get('endtime'))
        cross = jsonobj.get('cross')
        subject = jsonobj.get('subject')
        speakername = jsonobj.get('speakername')
        type = jsonobj.get('type')
        lang = jsonobj.get('lang')
        abstract = jsonobj.get('abstract')
        speakerintro = jsonobj.get('speakerintro')
        return Program(slot, room, starttime, endtime, cross, subject, speakername, type, lang, abstract, speakerintro)

    def __init__(self, slot, room, starttime, endtime, cross, subject, speakername, type, lang, abstract, speakerintro):
        self.slot = slot
        self.room = room
        self.starttime = starttime
        self.endtime = endtime
        self.cross = cross
        self.subject = subject
        self.speakername = speakername
        self.type = type
        self.lang = lang
        self.abstract = abstract
        self.speakerintro = speakerintro


class Room(object):
    @classmethod
    def de_json_list(cls, json_str):
        jsonobj = check_json(json_str)
        ret = []
        for program_json in jsonobj:
            ret.append(Room.de_json(program_json))
        return ret

    @classmethod
    def de_json(cls, json_obj):
        room = json_obj.get('room')
        name = json_obj.get('name')
        return Room(room, name)

    def __init__(self, room, name):
        self.room = room
        self.name = name


class ProgramType(object):
    @classmethod
    def de_json_list(cls, json_str):
        jsonobj = check_json(json_str)
        ret = []
        for program_json in jsonobj:
            ret.append(ProgramType.de_json(program_json))
        return ret

    @classmethod
    def de_json(cls, json_obj):
        type = json_obj.get('type')
        nameen = json_obj.get('nameen')
        namezh = json_obj.get('namezh')
        return ProgramType(type, nameen, namezh)

    def __init__(self, type, name_en, name_zh):
        self.type = type
        self.name_en = name_en
        self.name_zh = name_zh


class Sponsor(object):
    @classmethod
    def de_json_list(cls, json_str):
        jsonobj = check_json(json_str)
        ret = []
        for sponsor_json in jsonobj:
            ret.append(Sponsor.de_json(sponsor_json))
        return ret

    @classmethod
    def de_json(cls, json_obj):
        level = json_obj.get('level')
        place = json_obj.get('place')
        logolink = json_obj.get('logolink')
        logourl = json_obj.get('logourl')
        name_en = json_obj.get('nameen')
        name_zh = json_obj.get('namezh')
        intro_en = json_obj.get('introen')
        intro_zh = json_obj.get('introzh')
        return Sponsor(level, place, logolink, logourl, name_en, name_zh, intro_en, intro_zh)

    def __init__(self, level, place, logolink, logourl, name_en, name_zh, intro_en, intro_zh):
        self.level = level
        self.place = place
        self.logolink = logolink
        self.logourl = logourl
        self.name_en = name_en
        self.name_zh = name_zh
        self.intro_en = intro_en
        self.intro_zh = intro_zh


class Level(object):
    @classmethod
    def de_json_list(cls, json_str):
        jsonobj = check_json(json_str)
        ret = []
        for level_json in jsonobj:
            ret.append(Level.de_json(level_json))
        return ret

    @classmethod
    def de_json(cls, json_obj):
        level = json_obj.get('level')
        name_en = json_obj.get('nameen')
        name_zh = json_obj.get('namezh')
        return Level(level, name_en, name_zh)

    def __init__(self, level, name_en, name_zh):
        self.level = level
        self.name_zh = name_zh
        self.name_en = name_en


class Transport(object):
    @classmethod
    def de_json(cls, json_str):
        """
        This class's datastruct totally nightmare. Never parse it.
        :param json_str:
        :return:
        """
        jsonobj = check_json(json_str)
        return Transport(jsonobj)

    def __init__(self, jsonobj):
        self.json_obj = jsonobj
        self.lang_code = {'zh-TW': 'zh', 'en-US': 'en'}

    def get_transport_types(self, lang):
        """
        Get transport types.
        :param lang: language
        :return: string list. Transport types string.
        """
        transports = self.__get_transport_list()
        ret = []
        for transport in transports:
            ret.append(transport['title'][self.lang_code[lang]])
        return ret

    def get_transport_result(self, trans_type, lang):
        return self.__get_transport_content(trans_type)[self.lang_code[lang]]

    def __get_transport_list(self):
        return self.json_obj['transport']

    def __get_transport_content(self, trans_type):
        transports = self.__get_transport_list()
        for transport in transports:
            if trans_type == transport['title']['zh'] or trans_type == transport['title']['en']:
                return transport['content']
        return None


class Staff(object):
    @classmethod
    def de_json_list(cls, json_str):
        jsonobj = check_json(json_str)
        ret = []
        for staff_json in jsonobj:
            ret.append(Staff.de_json(staff_json))
        return ret

    @classmethod
    def de_json(cls, json_obj):
        team = json_obj.get('team')
        members = json_obj.get('members')
        return Staff(team, members)

    def __init__(self, team, members):
        self.team = team
        self.members = members
