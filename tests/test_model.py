# -*- coding: utf-8 -*-

import sys

sys.path.append('../')

from coscupbot import model


def test_de_json_program():
    program_json_str = open('test_data/program_test.json', 'r').read()
    program_list = model.Program.de_json_program_list(program_json_str)
    assert len(program_list) == 68


def test_de_json_program_data():
    program_json_str = open('test_data/program_test.json', 'r').read()
    program = model.Program.de_json_program_list(program_json_str)[0]
    assert program.slot == 'K0'
    assert program.room == 'R0'
    assert program.starttime.year == 2016
    assert program.starttime.day == 20
    assert program.starttime.hour == 1
    assert program.endtime.year == 2016
    assert program.endtime.day == 20
    assert program.endtime.hour == 2


def test_de_json_room():
    room_json_str = open('test_data/room_test.json', 'r').read()
    rooms = model.Room.de_json_list(room_json_str)
    assert len(rooms) == 9
    assert rooms[0].room == 'R0'
    assert rooms[0].name == '國際會議廳'
