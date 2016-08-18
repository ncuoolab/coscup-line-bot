# -*- coding: utf-8 -*-

import iso8601
import redis

SponsorKeyDic = {
    "vedkoprjdi": {
        'booth': 'D1',
        'name': '和沛移動',
        'url': 'https://www.hopebaytech.com/',
    },
    "dkmjijoji": {
        'booth': 'D2',
        'name': 'Gandi',
        'url': 'https://www.gandi.net/'
    },
    "djnfjdjfie": {
        'booth': 'G1',
        'name': "QNAP",
        'url': 'https://www.qnap.com/zh-tw/'
    },
    "vhjnjeda3er": {
        'booth': 'G10',
        'name': "捕夢網",
        'url': "http://www.pumo.com.tw/www/"
    },
    "dfdjfirnjnjh": {
        'booth': 'G8',
        'name': "Automattic",
        'url': "https://automattic.com/"
    },
    "dfjnj3ei31": {
        'booth': 'G2',
        'name': "Appier",
        'url': "http://www.appier.com/en/index.html"
    },
    "vnjbhkauj": {
        'booth': 'G6',
        'name': "Top Career",
        'url': "http://www.topcareer.jp/inter/"
    },
    "emijvbnruh": {
        'booth': 'G11',
        'name': "EITC",
        'url': "http://www.eitc.com.tw/"
    },
    "dfjrbenkuh": {
        'booth': 'G7',
        'name': "KKBOX",
        'url': "https://www.kkbox.com/about/zh-tw"
    },
    "dcfdjhuiyq": {
        'booth': 'G3',
        'name': "HDE",
        'url': "https://www.hde.co.jp/zh-hant/"
    },
    "dvuhjenqjb": {
        'booth': 'G4',
        'name': "MySQL",
        'url': "https://www.mysql.com/"
    },
    "qasddaojkrf": {
        'booth': 'G5',
        'name': "LINE",
        'url': "http://linecorp.com/zh-hant/"
    },
    "dfmk1njfu": {
        'booth': 'O',
        'name': "COSCUP",
        'url': "https://coscup.org"
    }
}

FINAL_SPONSOR = 'dfmk1njfu'


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
            if item:
                item = item[1]
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


def get_wit_datetime_count(request):
    ents = request['entities']
    datetimes = ents['datetime']
    return len(datetimes)


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


def get_wit_sponsor_name(request):
    ents = request['entities']
    sp = ents['sponsors'][0]['value']
    return sp

def get_wit_booth(request):
    ents = request['entities']
    sp = ents['booths'][0]['value']
    return sp
