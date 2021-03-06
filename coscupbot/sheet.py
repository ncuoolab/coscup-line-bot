# -*- coding: utf-8 -*-

import logging
import re

import gspread
from oauth2client.service_account import ServiceAccountCredentials

from coscupbot.model import *


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
        self.default_time_pos = (4, 2)
        self.refresh_time_pos = self.default_time_pos
        self.refresh_time_offset = (3, 1)
        self.update_time_pattern = 'Last updated at \d\d:\d\d on \d\d-\d\d-\d\d\d\d'
        self.update_time_str = 'Last updated at %H:%M on %m-%d-%Y'
        self.lang_set = (LanguageCode.zh_tw.lower(), LanguageCode.en_us.lower())

    def update_refresh_time(self, pos=None):
        self.erase_last_update_time()
        p = pos if pos else self.refresh_time_pos
        if not self.sheet_name:
            raise SheetError('Page name should be defined before updating time.')
        self.spreadsheet.worksheet(self.sheet_name).update_cell(p[0], p[1], datetime.datetime.now().strftime(self.update_time_str))
        logging.info('Update last access time, sheet: %s, pos: (%d, %d)' % (self.sheet_name, p[0], p[1]))

    def erase_last_update_time(self):
        if not self.sheet_name:
            raise SheetError('Page name should be defined before updating time.')
        amount_re = re.compile(self.update_time_pattern)
        cell = None
        try:
            cell = self.spreadsheet.worksheet(self.sheet_name).find(amount_re)
        except:
            cell = None
        if cell:
            self.spreadsheet.worksheet(self.sheet_name).update_cell(cell.row, cell.col, '')

    def retrieve_all_values(self):
        if not self.sheet_name:
            raise SheetError('Page name should be defined before retrieveing.')
        list_of_lists = self.spreadsheet.worksheet(self.sheet_name).get_all_values()
        self.update_refresh_time()
        return list_of_lists

class CommandSheetParser(SheetParser):
    def __init__(self, spreadsheet):
        super().__init__(spreadsheet)
        self.sheet_name = GoogleSheetName.Command
        self.refresh_time_pos = (1, 10)
        self.command_type = ('standard', 'humour')

    def parse_data(self):
        def get_command_response(tuple):
            nonsense = []
            if tuple[3] != '':
                nonsense.append(tuple[3])
            if tuple[5] != '':
                nonsense.append(tuple[5])
            return CommandResponse(nonsense, tuple[7])

        commands = {}
        re = []
        tuple_list = self.retrieve_all_values()
        for tuple in tuple_list[1:]:
            if not self.check_tuple_valid(tuple):
                continue
            # Check if humour.
            if tuple[2].lower()[6:] == self.command_type[1]:
                tuple[1] = tuple[1].strip() + '@'
            # Remove command type string.
            tuple[2] = tuple[2][:5]
            if tuple[1] not in commands:
                commands[tuple[1]] = {tuple[2]: [get_command_response(tuple)]}
            else:
                if tuple[2] in commands[tuple[1]]:
                    commands[tuple[1]][tuple[2]].append(get_command_response(tuple))
                else:
                    commands[tuple[1]][tuple[2]] = [get_command_response(tuple)]

        for command, v in commands.items():
            for lang, response in v.items():
                re.append(Command(lang, command, response))
        return re

    def check_tuple_valid(self, tuple):
        if tuple[1] == '' or tuple[2] == '' or tuple[7] == '':
            return False
        if tuple[2].lower()[:5] not in self.lang_set:
            return False
        if tuple[2].lower()[6:] not in self.command_type:
            return False
        return True


class RealtimeSheetParser(SheetParser):
    def __init__(self, spreadsheet):
        super().__init__(spreadsheet)
        self.refresh_time_pos = (1, 2)
        self.sheet_name = GoogleSheetName.Realtime

    def parse_data(self):
        commands = []
        tuple_list = self.retrieve_all_values()
        for tuple in tuple_list[1:]:
            if not self.check_tuple_valid(tuple):
                continue
            commands.append(tuple[0])
        self.clear_sheet(len(tuple_list))
        return commands

    def check_tuple_valid(self, tuple):
        if tuple[0] == '':
            return False
        return True

    def clear_sheet(self, row_count):
        sheet = self.spreadsheet.worksheet(self.sheet_name)
        for i in range(2, row_count + 1):
            sheet.update_cell(i, 1, '')


class NLPActionSheetParser(SheetParser):
    def __init__(self, spreadsheet):
        super().__init__(spreadsheet)
        self.refresh_time_pos = (1, 4)
        self.sheet_name = GoogleSheetName.NLPAction

    def parse_data(self):
        commands = {}
        re = []
        tuple_list = self.retrieve_all_values()
        for tuple in tuple_list[1:]:
            if not self.check_tuple_valid(tuple):
                continue
            if tuple[0] not in commands:
                commands[tuple[0]] = {tuple[1]: [tuple[2]]}
            else:
                if tuple[1] in commands[tuple[0]]:
                    commands[tuple[0]][tuple[1]].append(tuple[2])
                else:
                    commands[tuple[0]][tuple[1]] = [tuple[2]]

        for command, v in commands.items():
            for lang, response in v.items():
                re.append(NlpAction(lang, command, response))
        return re

    def check_tuple_valid(self, tuple):
        if tuple[0] == '' or tuple[1] == '' or tuple[2] == '':
            return False
        if tuple[1].lower() not in self.lang_set:
            return False
        return True


class TimeSheetParser(SheetParser):
    def __init__(self, spreadsheet):
        super().__init__(spreadsheet)
        self.sheet_name = GoogleSheetName.Time
        self.refresh_time_pos = (1, 3)
        self.time_str = '%Y-%m-%d %H:%M:%S'
        self.time_pattern = '\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d'

    def parse_data(self):
        commands = []
        tuple_list = self.retrieve_all_values()
        for tuple in tuple_list[1:]:
            if not self.check_tuple_valid(tuple):
                continue
            commands.append((datetime.datetime.strptime(tuple[0], self.time_str), tuple[1]))
        return commands

    def check_tuple_valid(self, tuple):
        if tuple[0] == '' or tuple[1] == '':
            return False
        if re.match(self.time_pattern, tuple[0]):
            return True
        else:
            return False


class SheetError(Exception):
    """
    If specific sheet name is not in predefined dict, it will be raised.
    """
    pass