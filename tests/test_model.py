# -*- coding: utf-8 -*-

import sys

sys.path.append('../')

from coscupbot import model


def test_de_json_program():
    program_json_str = open('test_data/program_test.json', 'r').read()
    program_list = model.Program.de_json_list(program_json_str)
    assert len(program_list) == 68


def test_de_json_program_data():
    program_json_str = open('test_data/program_test.json', 'r').read()
    program = model.Program.de_json_list(program_json_str)[0]
    assert program.slot == 'K0'
    assert program.room == 'R0'
    assert program.starttime.year == 2016
    assert program.starttime.day == 20
    assert program.starttime.hour == 9
    assert program.endtime.year == 2016
    assert program.endtime.day == 20
    assert program.endtime.hour == 10


def test_de_json_room():
    room_json_str = open('test_data/room_test.json', 'r').read()
    rooms = model.Room.de_json_list(room_json_str)
    assert len(rooms) == 9
    assert rooms[0].room == 'R0'
    assert rooms[0].name == '國際會議廳'


def test_de_json_program_type():
    pt_json_str = open('test_data/type_test.json', 'r').read()
    pts = model.ProgramType.de_json_list(pt_json_str)
    assert len(pts) == 12
    assert pts[0].type == 91
    assert pts[0].name_en == 'Unconf'
    assert pts[0].name_zh == 'Unconf'


def test_de_json_transport_zh():
    json_str = open('test_data/transport_test.json', 'r').read()
    trans = model.Transport.de_json(json_str)
    assert len(trans.get_transport_types('zh-TW')) == 5
    assert '搭乘捷運' in trans.get_transport_types('zh-TW')
