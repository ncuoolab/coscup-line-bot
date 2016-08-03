# -*- coding: utf-8 -*-

import iso8601
import redis


class RedisQueue(object):
    def __init__(self, name, namespace='queue', **redis_kwargs):
        self.__db = redis.Redis(**redis_kwargs)
        self.key = '%s:%s' % (namespace, name)

    def qsize(self):
        return self.__db.llen(self.key)

    def empty(self):
        return self.qsize() == 0

    def put(self, item):
        self.__db.rpush(self.key, item)

    def get(self, block=True, timeout=None):
        if block:
            item = self.__db.blpop(self.key, timeout=timeout)
        else:
            item = self.__db.lpop(self.key)

        return item

    def get_nowait(self):
        return self.get(False)


def chunks(l, n):
    n = max(1, n)
    return [l[i:i + n] for i in range(0, len(l), n)]


def to_utf8_str(byte):
    return byte.decode('utf-8')


def parse_wit_datime(dt):
    value = dt['value']
    return iso8601.parse_date(value)


def get_wit_datetimes(request):
    ents = request['entities']
    datetimes = ents['datetime']
    return parse_wit_datime(datetimes[0])


def get_wit_room(request):
    ents = request['entities']
    room = ents['room'][0]['value']
    return room


def get_wit_transport_type(request):
    ents = request['entities']
    room = ents['transport'][0]['value']
    return room
