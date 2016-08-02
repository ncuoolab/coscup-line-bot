# -*- coding: utf-8 -*-

import sys

sys.path.append('../')

from coscupbot import db, model, modules
import os
import pytest
import redis
import datetime
import pytz

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
class TestApiHelper:
    def test_find_program_by_room_time(self):
        program_json_str = open('test_data/program_test.json', 'r').read()
        ca = modules.CoscupInfoHelper(REDIS_URL)
        ca.programs = model.Program.de_json_program_list(program_json_str)
        time = datetime.datetime(year=2016, month=8, day=20, hour=10, minute=0, tzinfo=pytz.timezone('Asia/Taipei'))
        result = ca.find_program_by_room_time('R0', time)
        assert result.slot == 'K0'
