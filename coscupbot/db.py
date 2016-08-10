# -*- coding: utf-8 -*-

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

    def test_connection(self):
        r = self.__get_conn()
        r.ping()

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


class CommandError(Exception):
    """
    If command not in database will raise this error.
    """
    pass
