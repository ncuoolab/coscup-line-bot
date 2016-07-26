# -*- coding: utf-8 -*-

import sys

sys.path.append('../')

from coscupbot import db, model
import os
import pytest
import redis

should_skip = 'REDIS' not in os.environ

if not should_skip:
    REDIS_URL = os.environ['REDIS']


def get_dao():
    return db.Dao(REDIS_URL)


def gen_test_commands(num, language='zh_TW'):
    commands = []
    for i in range(0, num):
        response = ['resp%s-1' % i, 'resp%s-2' % i]
        cmd = model.Command(language, 'CMD%s' % i, response)
        commands.append(cmd)
    return commands


@pytest.mark.skipif(should_skip, reason="Redis connection url not configured")
class TestDb:
    @classmethod
    def teardown_class(cls):
        r = redis.from_url(REDIS_URL)
        r.flushall()

    def test_ping(self):
        get_dao().test_connection()

    def test_add_command_one_lang(self):
        get_dao().add_commands(gen_test_commands(10, 'zh_TW'))
        r = redis.from_url(REDIS_URL)
        assert 10 == len(r.keys('COMMAND::zh_TW::*'))

    def test_add_command_two_lang(self):
        get_dao().add_commands(gen_test_commands(10, 'zh_TW'))
        get_dao().add_commands(gen_test_commands(20, 'en'))
        r = redis.from_url(REDIS_URL)
        assert 10 == len(r.keys('COMMAND::zh_TW::*'))
        assert 20 == len(r.keys('COMMAND::en::*'))
        assert 30 == len(r.keys('COMMAND::*'))

    def test_delete_command(self):
        self.test_add_command_two_lang()
        get_dao().clear_all_command()
        r = redis.from_url(REDIS_URL)
        assert 0 == len(r.keys('COMMAND::*'))

    def test_get_command_response(self):
        cmd1 = model.Command('zh_TW', 'help', ['help', 'hi'])
        cmd2 = model.Command('zh_TW', 'hello', ['hello', 'world'])
        get_dao().add_commands([cmd1, cmd2])
        result = get_dao().get_command_responses('help', 'zh_TW')
        assert 'help' and 'hi' not in result
