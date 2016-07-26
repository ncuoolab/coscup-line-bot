# -*- coding: utf-8 -*-

import sys

sys.path.append('../')

from coscupbot import db
import os
import pytest

should_skip = 'REDIS' not in os.environ

if not should_skip:
    REDIS_URL = os.environ['REDIS']


@pytest.mark.skipif(should_skip, reason="Redis connection url not configured")
class TestDb:
    def test_ping(self):
        self.get_dao().test_connection()

    def get_dao(self):
        return db.Dao(REDIS_URL)
