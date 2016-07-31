# -*- coding: utf-8 -*-

import sys

sys.path.append('../')

from coscupbot import sheet
import os
import pytest
import gspread
import re

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
        pass

    def test_update_refresh_time(self):
        regular = 'Last updated at \d\d:\d\d on \d\d-\d\d-\d\d\d\d'
        parser = sheet.SheetParser(self.sheet.spreadsheet)
        parser.sheet_name = self.TEST_SHEET_NAME
        parser.update_refresh_time()
        assert re.match(regular, self.test_sheet.cell(*parser.refresh_time_pos).value)

    def test_erase_last_update_time(self):
        parser = sheet.SheetParser(self.sheet.spreadsheet)
        parser.sheet_name = self.TEST_SHEET_NAME
        parser.erase_last_update_time()
        parser.update_refresh_time()
        parser.erase_last_update_time()
        assert re.match('', self.test_sheet.cell(*parser.refresh_time_pos).value)

    def test_retrieve_all_values(self):
        expected = [['1','',''],
                    ['','1',''],
                    ['','','1'],
                    ['','1',''],
                    ['1','','']]
        pos = ((1, 1), (2, 2), (3, 3), (4, 2), (5, 1))
        for p in pos:
            self.test_sheet.update_cell(p[0], p[1], '1')
        parser = sheet.SheetParser(self.sheet.spreadsheet)
        parser.sheet_name = self.TEST_SHEET_NAME
        assert expected == parser.retrieve_all_values()

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
        tuple1 = ['help', 'zh-TW', 'tuple']
        tuple2 = ['help', 'en-US', 'tuple']
        tuple3 = ['', 'en-US', 'tuple1']
        tuple4 = ['help', '', 'tuple1']
        tuple5 = ['help', 'en-US', '']
        tuple6 = ['help', 'zh-tw', 'tuple']
        tuple7 = ['help', 'zh-cn', 'tuple']

        parser = sheet.NLPActionSheetParser(self.sheet.spreadsheet)
        assert True == parser.check_tuple_valid(tuple1)
        assert True == parser.check_tuple_valid(tuple2)
        assert False == parser.check_tuple_valid(tuple3)
        assert False == parser.check_tuple_valid(tuple4)
        assert False == parser.check_tuple_valid(tuple5)
        assert True == parser.check_tuple_valid(tuple6)
        assert False == parser.check_tuple_valid(tuple7)

    def test_check_tuple_valid_realtime(self):
        tuple1 = ['tuple']
        tuple2 = ['']

        parser = sheet.RealtimeSheetParser(self.sheet.spreadsheet)
        assert True == parser.check_tuple_valid(tuple1)
        assert False == parser.check_tuple_valid(tuple2)
        pass

    def test_check_tuple_valid_time(self):
        tuple1 = ['1984-01-01 00:00:00', 'tuple']
        tuple2 = ['1984-01-01 00:00:00', '']
        tuple3 = ['', 'tuple']
        tuple4 = ['1984-1-1 00:00:00', 'tuple']
        tuple5 = ['84-01-01 00:00:00', 'tuple']
        tuple6 = ['1984-01-01 00:00', 'tuple']
        tuple7 = ['1984/01/01 00:00:00', 'tuple']

        parser = sheet.TimeSheetParser(self.sheet.spreadsheet)
        assert True == parser.check_tuple_valid(tuple1)
        assert False == parser.check_tuple_valid(tuple2)
        assert False == parser.check_tuple_valid(tuple3)
        assert False == parser.check_tuple_valid(tuple4)
        assert False == parser.check_tuple_valid(tuple5)
        assert False == parser.check_tuple_valid(tuple6)
        assert False == parser.check_tuple_valid(tuple7)
        pass