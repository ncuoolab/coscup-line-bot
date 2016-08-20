# -*- coding: utf-8 -*-
import json
import logging
from threading import Lock

import redis

from coscupbot import utils


class Dao(object):
    def __init__(self, db_url):
        logging.info('Init redis dao use %s' % db_url)
        self.conn_pool = redis.ConnectionPool.from_url(url=db_url)
        self.test_connection()
        self.command_lock = Lock()
        self.nlp_lock = Lock()
        self.COMMAND_PATTERN = 'COMMAND::%s::%s'
        self.NLP_PATTERN = 'NLP::%s::%s'
        self.LANG_PATTERN = 'LANG::%s'
        self.HUMOUR_PATTERN = 'HUMOUR::%s'
        self.NEXT_STEP_PATTERN = 'NEXT::%s'
        self.GROUND_PATTERN = 'GROUND::%s'
        self.SESSION_PATTERN = 'SESSION::%s'
        self.CONTEXT_PATTERN = 'CONTEXT::%s'
        self.MESSAGE_RECORD = 'MSGRECORD'
        self.PHOTO_RECORD = 'PHOTOTACKED'
        self.NUMPHOTO_PATTERN = 'NUMPHOTO::%s'
        self.EDISON_ENABLE = 'EDISONENABLE'

    def is_edison_enable(self):
        self.__get_conn().setnx(self.EDISON_ENABLE, 1)
        result = int(self.__get_conn().get(self.EDISON_ENABLE))
        return result == 1

    def disable_edison(self):
        self.__get_conn().set(self.EDISON_ENABLE, 0)

    def enable_edison(self):
        self.__get_conn().set(self.EDISON_ENABLE, 1)

    def is_friend(self, mid):
        return self.__get_conn().exists(self.GROUND_PATTERN % mid)

    def get_num_of_photo(self, mid):
        self.__get_conn().setnx(self.NUMPHOTO_PATTERN % mid, 0)
        return int(self.__get_conn().get(self.NUMPHOTO_PATTERN % mid))

    def increase_num_of_photo(self, mid):
        self.__get_conn().incr(self.NUMPHOTO_PATTERN % mid, 1)

    def del_num_of_photo(self, mid):
        self.__get_conn().delete(self.NUMPHOTO_PATTERN % mid)

    def add_photo_record(self, record):
        self.__get_conn().lpush(self.PHOTO_RECORD, record)

    def get_photo_record_count(self):
        return int(self.__get_conn().llen(self.PHOTO_RECORD))

    def add_message_record(self, message):
        self.__get_conn().lpush(self.MESSAGE_RECORD, message)

    def get_message_record_count(self):
        return self.__get_conn().llen(self.MESSAGE_RECORD)

    def get_ground_player_count(self):
        return len(self.__get_conn().keys('GROUND*'))

    def get_num_of_friend(self):
        return len(self.__get_conn().keys('LANG*'))

    def test_connection(self):
        r = self.__get_conn()
        r.ping()

    def del_all_session(self):
        r = self.__get_conn()
        keys = r.keys('SESSION::*')
        if len(keys) == 0:
            return
        r.delete(*keys)

    def add_session(self, mid, session):
        self.__get_conn().set(self.SESSION_PATTERN % mid, session)

    def del_session(self, mid):
        self.__get_conn().delete(self.SESSION_PATTERN % mid)

    def get_session(self, mid):
        result = self.__get_conn().get(self.SESSION_PATTERN % mid)
        if result:
            return utils.to_utf8_str(result)
        return None

    def del_all_context(self):
        r = self.__get_conn()
        keys = r.keys('CONTEXT::*')
        if len(keys) == 0:
            return
        r.delete(*keys)

    def add_context(self, mid, context):
        self.__get_conn().set(self.CONTEXT_PATTERN % mid, json.dumps(context))

    def del_context(self, mid):
        self.__get_conn().delete(self.CONTEXT_PATTERN % mid)

    def get_context(self, mid):
        result = self.__get_conn().get(self.CONTEXT_PATTERN % mid)
        if result:
            return json.loads(utils.to_utf8_str(result))
        return None

    def del_lang_data(self, mid):
        self.__get_conn().delete(self.LANG_PATTERN % mid)

    def del_humour_data(self, mid):
        self.__get_conn().delete(self.HUMOUR_PATTERN % mid)

    def init_ground_data(self, mid):
        if self.__get_conn().exists(self.GROUND_PATTERN % mid):
            # avoid readd friend.
            return
        self.del_ground_data(mid)
        init_data = self.__init_ground_default_data()
        r = self.__get_conn()
        r.hmset(self.GROUND_PATTERN % mid, init_data)

    def checkin_ground(self, sp_id, mid):
        self.init_ground_data(mid)
        self.__get_conn().hset(self.GROUND_PATTERN % mid, sp_id, True)

    def get_ground_data(self, mid):
        ret = {}
        self.init_ground_data(mid)
        data = self.__get_conn().hgetall(self.GROUND_PATTERN % mid)
        for k, v in data.items():
            key = utils.to_utf8_str(k)
            if v == b'False':
                ret[key] = False
            elif v == b'True':
                ret[key] = True
            else:
                raise Exception('Can not convert key value %s  %s' % (k, v))
        return ret

    def del_ground_data(self, mid):
        key = self.GROUND_PATTERN % mid
        try:
            self.__get_conn().delete(key)
        except:
            pass

    def set_next_command(self, mid, lang, method_name, class_name):
        r = self.__get_conn()
        key = self.NEXT_STEP_PATTERN % mid
        value = lang + ":" + method_name + ":" + class_name
        r.set(key, value)

    def get_next_command(self, mid):
        result = self.__get_conn().get(self.NEXT_STEP_PATTERN % mid)
        if result:
            return utils.to_utf8_str(result)
        return None

    def del_next_command(self, mid):
        self.__get_conn().delete(self.NEXT_STEP_PATTERN % mid)

    def del_all_next_command(self):
        r = self.__get_conn()
        keys = r.keys('NEXT::*')
        if len(keys) == 0:
            return
        r.delete(*keys)

    def set_mid_lang(self, mid, lang):
        r = self.__get_conn()
        key = self.LANG_PATTERN % mid
        r.set(key, lang)

    def get_mid_lang(self, mid):
        result = self.__get_conn().get(self.LANG_PATTERN % mid)
        if result:
            return utils.to_utf8_str(result)
        return None

    def set_mid_humour(self, mid, is_humour):
        r = self.__get_conn()
        key = self.HUMOUR_PATTERN % mid
        if is_humour:
            r.set(key, 'y')
        else:
            r.set(key, 'n')

    def get_mid_humour(self, mid):
        result = self.__get_conn().get(self.HUMOUR_PATTERN % mid)
        if result:
            rs = utils.to_utf8_str(result)
            return rs == 'y'
        return None

    def add_commands(self, commands):
        """
        Add command list to redis db.
        :param commands:
        :return:
        """
        r = self.__get_conn()
        for cmd in commands:
            key = self.COMMAND_PATTERN % (cmd.language, cmd.command_str)
            r.rpush(key, *cmd.get_command_response_json_list())

    def clear_all_command(self):
        """
        This method will remove all commands in database.
        :return:
        """
        r = self.__get_conn()
        keys = r.keys('COMMAND::*')
        if len(keys) == 0:
            return
        r.delete(*keys)

    def update_commands(self, commands):
        """
        This method will clear all exist command in database. Then insert new commands.
        :param commands:
        :return:
        """
        self.command_lock.acquire()
        self.clear_all_command()
        self.add_commands(commands)
        self.command_lock.release()

    def update_NLP_command(self, actions):
        """
        This methos will clear all NLP command in database and insert new NLP commands.
        :param commands:
        :return:
        """
        self.nlp_lock.acquire()
        self.clear_all_nlp_action()
        self.add_nlp_action(actions)
        self.nlp_lock.release()

    def get_command_responses(self, cmd_str, lang='zh-TW', humour=False):
        """
        Get response array from database by command string.
        :param cmd_str: command. eg. 'help'
        :param lang: Language code. eg. 'zh_TW'
        :return: list of result
        """
        while self.command_lock.locked():
            pass

        key = self.COMMAND_PATTERN % (lang, cmd_str)
        if humour:
            key += '@'
        result = self.__get_conn().lrange(key, 0, -1)
        if result is None:
            raise CommandError('Command %s response is None.' % key)
        if len(result) == 0:
            raise CommandError('Command %s has no response.' % key)
        return result

    def add_nlp_action(self, actions):
        """
        Add nlp actions to redis db.
        :param commands:
        :return:
        """
        r = self.__get_conn()
        for action in actions:
            key = self.NLP_PATTERN % (action.language, action.action_str)
            r.rpush(key, *action.response)

    def clear_all_nlp_action(self):
        """
        This method will remove all commands in database.
        :return:
        """
        r = self.__get_conn()
        keys = r.keys('NLP::*')
        if len(keys) == 0:
            return
        r.delete(*keys)

    def get_nlp_response(self, action, lang='zh-TW'):
        while self.nlp_lock.locked():
            pass

        key = self.NLP_PATTERN % (lang, action)
        result = self.__get_conn().lrange(key, 0, -1)
        if result is None:
            raise CommandError('NLPAction %s response is None.' % key)
        if len(result) == 0:
            raise CommandError('NLPAction %s has no response.' % key)
        return result

    def add_user_mid(self, mid):
        self.__get_conn().hset('MID', mid, mid)

    def get_all_user_mid(self):
        mid_dic = self.__get_conn().hgetall('MID')
        return [k.decode("utf-8") for k in mid_dic.keys()]

    def save_coscup_api_data(self, typename, json_str):
        key = 'CONFINFO::%s' % typename
        self.__get_conn().set(key, json_str)

    def get_coscup_api_data(self, typename):
        key = 'CONFINFO::%s' % typename
        return utils.to_utf8_str(self.__get_conn().get(key))

    def __get_conn(self):
        return redis.Redis(connection_pool=self.conn_pool)

    def __init_ground_default_data(self):
        ret = {}
        for key in utils.SponsorKeyDic:
            ret[key] = False
        return ret


class CommandError(Exception):
    """
    If command not in database will raise this error.
    """
    pass
