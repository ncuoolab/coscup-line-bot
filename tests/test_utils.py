# -*- coding: utf-8 -*-

import sys

sys.path.append('../')

from coscupbot import utils


def test_chunks():
    list = [1, 2, 3, 4, 5, 6, 7, 8]
    result = utils.chunks(list, 2)
    assert 4 == len(result)
    assert 1 in result[0]
    assert 3 not in result[0]
