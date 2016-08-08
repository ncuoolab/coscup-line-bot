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

