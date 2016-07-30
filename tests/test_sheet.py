# -*- coding: utf-8 -*-

import sys

sys.path.append('../')

from coscupbot import sheet
import os
import pytest
import gspread

should_skip = 'SHEET_CREDENTIAL_PATH' not in os.environ or 'SHEET_NAME' not in os.environ

if not should_skip:
    SHEET_CREDENTIAL_PATH = os.environ['SHEET_CREDENTIAL_PATH']
    SHEET_NAME = os.environ['SHEET_NAME']


def get_sheet():
    return sheet.Sheet(SHEET_CREDENTIAL_PATH, SHEET_NAME)

@pytest.mark.skipif(should_skip, reason="Google sheet credential path or name not configured")
class TestSheet:

    def setup_method(self, test_method):
        self.sheet = get_sheet()
        self.TEST_SHEET_NAME = 'test_sheet'
        self.test_sheet = self.sheet.spreadsheet.add_worksheet(title=self.TEST_SHEET_NAME, rows="50", cols="10")

    def teardown_method(self, test_method):
        self.sheet.spreadsheet.del_worksheet(self.test_sheet)

    def test_check_tuple_valid_command(self):
        tuple1 = ['', 'help', 'zh-TW', 'tuple']
        tuple2 = ['', 'help', 'en-US', 'tuple']
        tuple3 = ['', '', 'en-US', 'tuple1']
        tuple4 = ['', 'help', '', 'tuple1']
        tuple5 = ['', 'help', 'en-US', '']
        tuple6 = ['', 'help', 'zh-tw', 'tuple']
        tuple7 = ['', 'help', 'zh-cn', 'tuple']

        parser = sheet.CommandSheetParser(self.sheet.spreadsheet)
        assert True == parser.check_tuple_valid(tuple1)
        assert True == parser.check_tuple_valid(tuple2)
        assert False == parser.check_tuple_valid(tuple3)
        assert False == parser.check_tuple_valid(tuple4)
        assert False == parser.check_tuple_valid(tuple5)
        assert True == parser.check_tuple_valid(tuple6)
        assert False == parser.check_tuple_valid(tuple7)


    def test_check_tuple_valid_NLPAction(self):
        pass

    def test_check_tuple_valid_realtime(self):
        pass