'''
    TypeOracle: a fuzzer for PDF Readers' script engine
    Copyright (C) 2022 Suyue Guo(guosuyue@ruc.edu.cn), Xinyu Wan(wxyxsx@ruc.edu.cn), Wei You(youwei@ruc.edu.cn)

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import os
import json

import pykd

CUR_PATH = r'C:\Users\wxy\TypeOracle\Tools\TypeInfer\foxit\3.arg_probe'

nothing_start = 0x9d6580  # + 0x400000
# start of app.platform (wrapper)

toolbar_start = 0xa0ab70
# start of app.platform (real)
toolbar_ret = 0x9d682c
# end of app.platform (wrapper)

dispatcher_start = 0x2410169
dispatcher_end = 0x241016b

setter_start = 0x24103d0
setter_end = 0x24103d2

jsonkey1 = 0x240a57b
# push dword ptr [eax]
jsonkey2 = 0x240c8fc
# push dword ptr [eax]

rbool = 0x246d657
# test al, FEh
rnum = 0x2430f29
# mov ecx, [esi]
rstr = 0x2412b2a
# mov [ebp-14h], ecx
rarr = 0x2635aea
# mov ecx, [ecx+bh]

img_base = 0

flag = 0
order = 0

bp_lst = []
tmp_bp_lst = []

bool_lst = []
num_lst = []
str_lst = []
arr_lst = []

key_lst = []


def write_json(content, fname):
    with open(os.path.join(CUR_PATH, str(fname)+'.json'), 'w') as f:
        f.write(json.dumps(content))


def use_less():
    pass


def start_rec():
    global flag
    flag = (flag+1) % 4

    if flag == 2:
        global order, bp_lst
        # print('s',order)
        order += 1

        b1 = pykd.setBp(dispatcher_start+img_base, real_start)
        b2 = pykd.setBp(dispatcher_end+img_base, real_end)
        b3 = pykd.setBp(setter_start+img_base, real_start)
        b4 = pykd.setBp(setter_end+img_base, real_end)
        bp_lst = [b1, b2, b3, b4]


def end_rec():
    global flag
    flag = (flag+1) % 4

    if flag == 3:

        global order, bp_lst, tmp_bp_lst
        global bool_lst, num_lst, str_lst, arr_lst, key_lst

        tmpdic = {'key': key_lst}

        if order in [1, 2]:
            tmpdic['val'] = bool_lst
        elif order in [3, 4]:
            tmpdic['val'] = num_lst
        elif order in [5, 6]:
            tmpdic['val'] = str_lst
        elif order in [7, 8]:
            tmpdic['val'] = arr_lst

        write_json(tmpdic, order)

        order = order % 9

        bp_lst = []
        tmp_bp_lst = []

        bool_lst = []
        num_lst = []
        str_lst = []
        arr_lst = []
        key_lst = []


def real_start():
    bp1 = pykd.setBp(jsonkey1+img_base, key_rec1)
    bp2 = pykd.setBp(jsonkey2+img_base, key_rec2)

    global tmp_bp_lst
    tmp_bp_lst = [bp1, bp2]

    if order in [1, 2]:
        bp3 = pykd.setBp(rbool+img_base, bool_rec)
        tmp_bp_lst.append(bp3)
    elif order in [3, 4]:
        bp3 = pykd.setBp(rnum+img_base, num_rec)
        tmp_bp_lst.append(bp3)
    elif order in [5, 6]:
        bp3 = pykd.setBp(rstr+img_base, str_rec)
        tmp_bp_lst.append(bp3)
    elif order in [7, 8]:
        bp3 = pykd.setBp(rarr+img_base, arr_rec)
        tmp_bp_lst.append(bp3)


def real_end():
    global tmp_bp_lst
    tmp_bp_lst = []


def bool_rec():
    val = pykd.reg('al')

    global bool_lst
    bool_lst.append(val)


def num_rec():
    val = pykd.loadDWords(pykd.reg('esi'), 1)[0]

    global num_lst
    num_lst.append(val)


def str_rec():
    val = pykd.reg('ecx')

    global str_lst
    str_lst.append(val)


def arr_rec():
    val = pykd.loadDWords(pykd.reg('ecx')+0xb, 1)[0]

    global arr_lst
    arr_lst.append(val)


def key_rec1():
    val = pykd.loadCStr(pykd.loadDWords(pykd.reg('eax'), 1)[0])

    global key_lst
    key_lst.append(val)


def key_rec2():
    val = pykd.loadCStr(pykd.loadDWords(pykd.reg('eax'), 1)[0])

    global key_lst
    key_lst.append(val)


if __name__ == '__main__':
    pykd.removeAllBp()

    img_base = pykd.module('FoxitReader').begin()

    b1 = pykd.setBp(nothing_start+img_base, use_less)
    b2 = pykd.setBp(toolbar_start+img_base, end_rec)
    b3 = pykd.setBp(toolbar_ret+img_base, start_rec)

    pykd.go()
