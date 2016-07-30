# -*- coding: utf-8 -*-

import logging
import gspread
import datetime
import re
from coscupbot.model import *
from oauth2client.service_account import ServiceAccountCredentials

class Sheet(object):
    def __init__(self, credential_path, spreadsheet_name):
        scope = ['https://spreadsheets.google.com/feeds']
        credentials = ServiceAccountCredentials.from_json_keyfile_name(credential_path, scope)
        self.gc = gspread.authorize(credentials)
        logging.info('Sheet service client authorized, credential path: %s' % credential_path)
        self.spreadsheet = self.gc.open(spreadsheet_name)
        pass

    def parse_all_data(self):
        re = {}
        re[GoogleSheetName.Command] = CommandSheetParser(self.spreadsheet).parse_data()
        re[GoogleSheetName.Realtime] = RealtimeSheetParser(self.spreadsheet).parse_data()
        re[GoogleSheetName.NLPAction] = NLPActionSheetParser(self.spreadsheet).parse_data()
        re[GoogleSheetName.Time] = TimeSheetParser(self.spreadsheet).parse_data()
        return re


class SheetParser(object):
    def __init__(self, spreadsheet):
        self.spreadsheet = spreadsheet
        self.sheet_name = None
        self.default_time_pos = (4, 1)
        self.refresh_time_pos = self.default_time_pos
        self.refresh_time_offset = (3, 0)

    def update_refresh_time(self, pos=None):
        p = pos if pos else self.refresh_time_pos
        if not self.sheet_name:
            raise SheetError('Page name should be defined before updating time.')
        self.spreadsheet.worksheet(self.sheet_name).update_cell(p[0], p[1], datetime.datetime.now().strftime('Last updated at %H:%M on %m/%d/%Y'))
        logging.info('Update last access time, sheet: %s, pos: (%d, %d)' % (self.sheet_name, p[0], p[1]))

    def erase_last_update_time(self):
        if not self.sheet_name:
            raise SheetError('Page name should be defined before updating time.')
        if re.match('Last updated at \d\d:\d\d on \d\d\/\d\d\/\d\d\d\d',
                    self.spreadsheet.worksheet(self.sheet_name).cell(*self.refresh_time_pos).value):
            self.spreadsheet.worksheet(self.sheet_name).update_cell(self.refresh_time_pos[0], self.refresh_time_pos[1], '')

    def retrieve_all_values(self):
        if not self.sheet_name:
            raise SheetError('Page name should be defined before retrieveing.')
        list_of_lists = self.spreadsheet.worksheet(self.sheet_name).get_all_values()
        self.set_refresh_time_pos(list_of_lists)
        return list_of_lists

    def set_refresh_time_pos(self, list_of_lists):
        if len(list_of_lists) > 0:
            self.refresh_time_pos = (len(list_of_lists) + self.refresh_time_offset[0],
                                     len(list_of_lists[0]) + self.refresh_time_offset[1])
        else:
            self.refresh_time_pos = self.default_time_pos


class CommandSheetParser(SheetParser):
    def __init__(self, spreadsheet):
        super().__init__(spreadsheet)
        self.sheet_name = GoogleSheetName.Command
        self.lang_set = ('en-us', 'zh-tw')

    def parse_data(self):
        commands = {}
        re = []
        tuple_list = self.retrieve_all_values()
        for tuple in tuple_list[1:]:
            if not self.check_tuple_valid(tuple):
                continue
            if tuple[1] not in commands:
                commands[tuple[1]] = {tuple[2]: [tuple[3]]}
            else:
                if tuple[2] in commands[tuple[1]]:
                    commands[tuple[1]][tuple[2]].append(tuple[3])
                else:
                    commands[tuple[1]][tuple[2]] = [tuple[3]]

        for command, v in commands.items():
            for lang, response in v.items():
                re.append(Command(lang, command, response))
        return re

    def check_tuple_valid(self, tuple):
        if tuple[1] == '' or tuple[2] == '' or tuple[3] == '':
            return False
        if tuple[2].lower() not in self.lang_set:
            return False
        return True


class RealtimeSheetParser(SheetParser):
    def __init__(self, spreadsheet):
        super().__init__(spreadsheet)
        self.sheet_name = GoogleSheetName.Realtime
        pass

    def parse_data(self):
        pass

    def check_tuple_valid(self):
        pass


class NLPActionSheetParser(SheetParser):
    def __init__(self, spreadsheet):
        super().__init__(spreadsheet)
        self.sheet_name = GoogleSheetName.NLPAction
        pass

    def parse_data(self):
        pass

    def check_tuple_valid(self):
        pass


class TimeSheetParser(SheetParser):
    def __init__(self, spreadsheet):
        super().__init__(spreadsheet)
        self.sheet_name = GoogleSheetName.Time
        pass

    def parse_data(self):
        pass

    def check_tuple_valid(self):
        pass


class SheetError(Exception):
    """
    If specific sheet name is not in predefined dict, it will be raised.
    """
    pass