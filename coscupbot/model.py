# -*- coding: utf-8 -*-
import json


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


class GoogleSheetName(object):
    Command = 'COMMAND'
    NLPAction = 'NLP_ACTION'
    Realtime = 'REALTIME'
    Time = 'TIME'


class Program(object):
    @classmethod
    def de_json_program_list(cls, json_string):
        jsonobj = check_json(json_string)
        ret = []
        for program_json in jsonobj:
            ret.append(Program.de_json_program(program_json))
        return ret

    @classmethod
    def de_json_program(cls, jsonobj):
        slot = jsonobj.get('slot')
        room = jsonobj.get('room')
        starttime = 
        pass

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
