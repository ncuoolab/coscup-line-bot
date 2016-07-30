# -*- coding: utf-8 -*-

import logging
import gspread
import datetime
from coscupbot.model import *
from oauth2client.service_account import ServiceAccountCredentials

class Sheet(object):
    def __init__(self, credential_path, spreadsheet_name):
        scope = ['https://spreadsheets.google.com/feeds']
        credentials = ServiceAccountCredentials.from_json_keyfile_name(credential_path, scope)
        self.gc = gspread.authorize(credentials)
        logging.info('Sheet service client authorized, credential path: %s' % credential_path)
        self.spreadsheet = self.gc.open(spreadsheet_name)
        self.page_parsers = [CommandPageParser(self.spreadsheet),
                             RealtimePageParser(self.spreadsheet),
                             NLPActionPageParser(self.spreadsheet)]
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

    def parse_all_data(self):
        re = []
        re.append(self.parse_command_page)
        re.append(self.parse_realtime_page)
        re.append(self.parse_NLPAction_page)
        return re
        pass


class PageParser(object):
    def __init__(self, spreadsheet):
        self.spreadsheet = spreadsheet
        self.page_name = None
        self.refresh_time_pos = (1, 4)
        self.refresh_time_offset = (0, 3)

    def retrieve_all_values(self):
        if not self.page_name:
            raise SheetError('Page name should be defined before retrieveing.')
        list_of_lists = self.spreadsheet.worksheet(self.page_name).get_all_values()
        self.refresh_time_pos = (len(list_of_lists[0]) + self.refresh_time_offset[0] + 1,
                                 len(list_of_lists) + self.refresh_time_offset[1] + 1)
        return list_of_lists


class CommandPageParser(PageParser):
    def __init__(self, spreadsheet):
        super().__init__(spreadsheet)
        self.page_name = GoogleSheetName.Command

    def parse_data(self):
        commands = []
        tuple_list = self.retrieve_all_values()
        for tuple in tuple_list:
            if not self.check_tuple_valid():
                continue
            commands.append(Command(tuple[2], tuple[1], tuple[3]))
        return commands

    def check_tuple_valid(self, tuple):
        if tuple[1] == '' or tuple[2] == '' or tuple[3] == '':
            return False
        if tuple[2].lower() not in self.lang_set:
            return False
        return True


class RealtimePageParser(PageParser):
    def __init__(self, spreadsheet):
        super().__init__(spreadsheet)
        self.page_name = GoogleSheetName.Realtime
        pass


class NLPActionPageParser(PageParser):
    def __init__(self, spreadsheet):
        super().__init__(spreadsheet)
        self.page_name = GoogleSheetName.NLPAction
        pass


class SheetError(Exception):
    """
    If specific sheet name is not in predefined dict, it will be raised.
    """
    pass