# -*- coding: utf-8 -*-

import logging
import gspread
import datetime
from oauth2client.service_account import ServiceAccountCredentials

class Sheet(object):
    def __init__(self, credential_path, spreadsheet_name):
        scope = ['https://spreadsheets.google.com/feeds']
        credentials = ServiceAccountCredentials.from_json_keyfile_name(credential_path, scope)
        self.gc = gspread.authorize(credentials)
        logging.info('Sheet service client authorized, credential path: %s' % credential_path)
        self.spreadsheet = self.gc.open(spreadsheet_name)
        self.refresh_time_pos = (1, 1)
        self.COMMNAD_SHEET_NAME = 'COMMAND'
        self.REALTIME_SHEET_NAME = 'NLP_ACTION'
        pass

    def update_refresh_time(self, sheet_name=None, pos=None):
        p = pos if pos else self.refresh_time_pos
        sheet = None
        if sheet_name:
            sheet = self.spreadsheet.worksheet(sheet_name)
        else:
            sheet = self.spreadsheet.worksheet(self.COMMNAD_SHEET_NAME)

        sheet.update_cell(p[0], p[1], datetime.datetime.now().strftime('Last updated at %I:%M%p on %m/%d/%Y'))
        pass
