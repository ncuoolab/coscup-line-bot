# -*- coding: utf-8 -*-

import logging
import redis
from threading import Lock


class Dao(object):
    def __init__(self, db_url):
        logging.info('Init redis dao use %s' % db_url)
        self.conn_pool = redis.ConnectionPool.from_url(url=db_url)
        self.test_connection()
        self.command_lock = Lock()
        self.COMMAND_PATTERN = 'COMMAND::%s::%s'

    def test_connection(self):
        r = self.__get_conn()
        r.ping()

    def add_commands(self, commands):
        """
        Add command list to redis db.
        :param commands:
        :return:
        """
        r = self.__get_conn()
        for cmd in commands:
            key = self.COMMAND_PATTERN % (cmd.language, cmd.command_str)
            r.rpush(key, cmd.response)

    def clear_all_command(self):
        """
        This method will remove all commands in database.
        :return:
        """
        r = self.__get_conn()
        keys = r.keys('COMMAND::*')
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

    def update_NLP_command(self, commands):
        """
        This methos will clear all NLP command in database and insert new NLP commands.
        :param commands:
        :return:
        """
        pass

    def get_command_responses(self, cmd_str, lang='zh_TW'):
        """
        Get response array from database by command string.
        :param cmd_str: command. eg. 'help'
        :param lang: Language code. eg. 'zh_TW'
        :return: list of result
        """
        while self.command_lock.locked():
            pass

        key = self.COMMAND_PATTERN % (lang, cmd_str)
        result = self.__get_conn().lrange(key, 0, -1)
        if result is None:
            raise CommandError('Command %s response is None.' % key)
        if len(result) == 0:
            raise CommandError('Command %s has no response.' % key)
        return result

    def get_nlp_response(self, action, lang='zh_TW'):
        while self.command_lock.locked():
            pass

        key = 'NLP::%s::%s' % (lang, action)
        result = self.__get_conn().lrange(key, 0, -1)
        if result is None:
            raise CommandError('NLPAction %s response is None.' % key)
        if len(result) == 0:
            raise CommandError('NLPAction %s has no response.' % key)
        return result

    def __get_conn(self):
        return redis.Redis(connection_pool=self.conn_pool)


class CommandError(Exception):
    """
    If command not in database will raise this error.
    """
    pass
