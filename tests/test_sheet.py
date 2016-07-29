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

    def test_update_refresh_time(self):
        pos = (1, 1)
        self.test_sheet.update_cell(pos[0], pos[1], '')
        self.sheet.update_refresh_time(sheet_name=self.TEST_SHEET_NAME, pos=pos)
        r = self.test_sheet.cell(*pos).value
        assert 'Last updated at' in r
