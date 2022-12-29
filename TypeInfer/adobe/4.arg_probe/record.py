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

# .load pykd;!py -g C:\Users\wxy\Desktop\extadobe\record.py

CUR_PATH = r'C:\Users\wxy\TypeOracle\Tools\TypeInfer\adobe\4.arg_probe'
# absolute path

toolbar_start = 0xcae20
# app.toolbar  push 0Ch
toolbar_ret = 0xcaf33
# app.toolbar  retn

dispatcher_start = 0x52ab3
# method  call ebx
dispatcher_end = 0x52ab5
# method  add esp,10h

setter_start = 0x3e197
setter_end = 0x3e199
# unused

jsonkey1 = 0x5bf57
# push [ebp+c] wchar_t*
jsonkey2 = 0x416ce
# push esi

rbool = 0x5be73
# test ecx,ecx
rnum = 0x53d68
# mov dword ptr [ebp-8], ecx
rstr = 0x3ce39
# mov [eax], ecx
rarr = 0x539c0
# mov eax,[ebp-4]

img_base = 0
# for escript.api

flag = 0
# watch point for app.toolbar

order = 0
# order for arguments

bp_lst = []
# store bp for watch points
tmp_bp_lst = []
# store bp for type indicators

bool_lst = []
num_lst = []
str_lst = []
arr_lst = []

key_lst = []


def write_json(content, fname):
    with open(os.path.join(CUR_PATH, str(fname)+'.json'), 'w') as f:
        f.write(json.dumps(content))


# toolbar ret
def start_rec():
    global flag
    flag = (flag+1) % 4
    # 0 {app.toolbar 1} 2 {app.toolbar 3} 4->0

    if flag == 2:
        global order, bp_lst
        order += 1
        # cycle times
        b1 = pykd.setBp(dispatcher_start+img_base, real_start)
        b2 = pykd.setBp(dispatcher_end+img_base, real_end)
        b3 = pykd.setBp(setter_start+img_base, real_start)
        b4 = pykd.setBp(setter_end+img_base, real_end)
        bp_lst = [b1, b2, b3, b4]


# toolbar start
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
    val = pykd.reg('ecx')

    global bool_lst
    bool_lst.append(val)


def num_rec():
    val = pykd.reg('ecx')

    global num_lst
    num_lst.append(val)


def str_rec():
    val = pykd.reg('ecx')

    global str_lst
    str_lst.append(val)


def arr_rec():
    val = pykd.loadDWords(pykd.reg('ebp')-0x4, 1)[0]

    global arr_lst
    arr_lst.append(val)


def key_rec1():
    val = pykd.loadCStr(pykd.loadDWords(pykd.reg('ebp')+0xc, 1)[0])

    global key_lst
    key_lst.append(val)


def key_rec2():
    val = pykd.loadWStr(pykd.reg('esi'))

    global key_lst
    key_lst.append(val)


if __name__ == '__main__':
    pykd.removeAllBp()

    img_base = pykd.module('escript').begin()

    b1 = pykd.setBp(toolbar_start+img_base, end_rec)
    b2 = pykd.setBp(toolbar_ret+img_base, start_rec)

    pykd.go()
