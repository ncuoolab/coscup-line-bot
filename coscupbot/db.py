# -*- coding: utf-8 -*-

import logging
import redis


class Dao(object):
    def __init__(self, db_url):
        logging.info('Init redis dao use %s' % db_url)
        self.conn_pool = redis.ConnectionPool.from_url(url=db_url)
        self.test_connection()
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

    def get_command_responses(self, cmd_str, lang='zh_TW'):
        """
        Get response array from database by command string.
        :param cmd_str: command. eg. 'help'
        :param lang: Language code. eg. 'zh_TW'
        :return: list of result
        """
        key = self.COMMAND_PATTERN % (lang, cmd_str)
        result = self.__get_conn().lrange(key, 0, -1)
        if result is None:
            raise CommandError('Command %s response is None.' % key)
        if len(result) == 0:
            raise CommandError('Command %s has no response.' % key)
        return result

    def __get_conn(self):
        return redis.Redis(connection_pool=self.conn_pool)


class CommandError(Exception):
    """
    If command not in database will raise this error.
    """
    pass
