# -*- coding: utf-8 -*-

import logging
import redis


class Dao(object):
    def __init__(self, db_url):
        logging.info('Init redis dao use %s' % db_url)
        self.conn_pool = redis.ConnectionPool.from_url(url=db_url)
        self.test_connection()

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
            key = 'COMMAND::%s::%s' % (cmd.language, cmd.command_str)
            r.rpush(key, cmd.response)

    def clear_all_command(self):
        """
        This method will remove all commands in database.
        :return:
        """
        r = self.__get_conn()
        keys = r.keys('COMMAND::*')
        r.delete(*keys)

    def __get_conn(self):
        return redis.Redis(connection_pool=self.conn_pool)


