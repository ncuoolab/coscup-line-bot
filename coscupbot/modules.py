# -*- coding: utf-8 -*-

from coscupbot import api, db

class MessageController(object):
    def __init__(self, bot_api, db_url):
        self.bot_api = bot_api
        self.dao = db.Dao(db_url)
