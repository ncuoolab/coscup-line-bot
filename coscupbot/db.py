# -*- coding: utf-8 -*-

import logging
import redis


class Dao(object):
    def __init__(self, db_url):
        logging.info('Init redis dao use %s' % db_url)
        self.conn_pool = redis.ConnectionPool.from_url(url=db_url)
        self.test_connection()

    def test_connection(self):
        r = redis.Redis(connection_pool=self.conn_pool)
        r.ping()

