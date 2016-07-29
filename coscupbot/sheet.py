# -*- coding: utf-8 -*-

import logging
import gspread
import datetime
from coscupbot.model import GoogleSheetName
from oauth2client.service_account import ServiceAccountCredentials

class Sheet(object):
    def __init__(self, credential_path, spreadsheet_name):
        scope = ['https://spreadsheets.google.com/feeds']
        credentials = ServiceAccountCredentials.from_json_keyfile_name(credential_path, scope)
        self.gc = gspread.authorize(credentials)
        logging.info('Sheet service client authorized, credential path: %s' % credential_path)
        self.spreadsheet = self.gc.open(spreadsheet_name)
        self.refresh_time_pos = (1, 4)
        self.refresh_time_offset = (0, 3)
        pass

    def update_refresh_time(self, sheet_name=None, pos=None):
        p = pos if pos else self.refresh_time_pos
        sheet = None
        if sheet_name:
            sheet = self.spreadsheet.worksheet(sheet_name)
        else:
            sheet = self.spreadsheet.worksheet(GoogleSheetName.Command)

        sheet.update_cell(*p, datetime.datetime.now().strftime('Last updated at %I:%M%p on %m/%d/%Y'))
        logging.info('Update last access time, sheet: %s, pos: (%d, %d)' % (sheet, p[0], p[1]))
        pass

    def get_all_values_from_specific_sheet(self, sheet_name):
        func = {
            GoogleSheetName.Command:    self.__get_all_values_from_command_page,
            GoogleSheetName.NLPAction:  self.__get_all_values_from_NLPAction_page,
            GoogleSheetName.Realtime:   self.__get_all_values_from_realtime_page
        }.get(sheet_name)
        if not func:
            raise SheetError('Sheet name %s is not found.' % sheet_name)
        return func()

    def __get_all_values_from_command_page(self):
        list_of_lists = self.spreadsheet.worksheet(GoogleSheetName.Command).get_all_values()
        self.refresh_time_pos = (len(list_of_lists[0]) + self.refresh_time_offset[0] + 1,
                                 len(list_of_lists) + self.refresh_time_offset[1] + 1)
        pass

    def __get_all_values_from_realtime_page(self):
        pass

    def __get_all_values_from_NLPAction_page(self):
        pass


class SheetError(Exception):
    """
    If specific sheet name is not in predefined dict, it will be raised.
    """
    pass