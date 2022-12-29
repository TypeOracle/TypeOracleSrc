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

CUR_PATH = r'C:\Users\wxy\TypeOracle\Tools\TypeInfer\adobe\3.generic_object\stage2'

toolbar_start = 0xcae20
toolbar_ret = 0xcaf33
dispatcher_call = 0x52ab3
dispatcher_next = 0x52ab5

img_base = 0

toolbar_flag = 0
dispatcher_flag = 0

addrlst = []

bp_lst1 = []
bp_lst2 = []

bp_dic = {}
res_dic = {}


def start_rec1():
    global toolbar_flag
    toolbar_flag = (toolbar_flag+1) % 4
    if toolbar_flag == 2:

        print('[=] 1st app.toolbar end, start record')

        bp1 = pykd.setBp(dispatcher_call+img_base, start_rec2)
        bp2 = pykd.setBp(dispatcher_next+img_base, end_rec2)
        global bp_lst1
        global bp_lst2
        bp_lst1 = [bp1, bp2]
        bp_lst2 = []


def end_rec1():
    global toolbar_flag
    toolbar_flag = (toolbar_flag+1) % 4
    if toolbar_flag == 3:

        print('[=] 2rd app.toobar start, end record')

        global bp_lst1
        global bp_lst2
        bp_lst1 = []
        bp_lst2 = []


def start_rec2():
    if toolbar_flag == 2:

        global res_dic
        res_dic = {}
        print('[==] api start, init result')

        global bp_lst2
        for addr in bp_dic:
            val = bp_dic[addr]
            bp = pykd.setBp(int(addr, 16)+img_base, read_addr(val))
            bp_lst2.append(bp)


def end_rec2():
    if toolbar_flag == 2:

        global bp_lst2
        bp_lst2 = []
        print('[==] api end, clear breakpoint')
        newdic = {}
        for addr in res_dic:
            newdic[addr] = sorted(list(res_dic[addr]))
        with open(os.path.join(CUR_PATH, 'result.json'), 'w') as f:
            f.write(json.dumps(newdic))
        print('[+] write dic to result.json')


def read_addr(cmd):
    def real_func():
        tmp = pykd.dbgCommand(cmd)
        val = tmp.strip().split(' ')[-1]
        addr = hex(pykd.reg('eip')-img_base)[2:]

        global res_dic
        if addr not in res_dic:
            res_dic[addr] = set()
        res_dic[addr].add(val)
    # todo
    return real_func


if __name__ == '__main__':

    pykd.removeAllBp()

    with open(os.path.join(CUR_PATH, 'bp.json'), 'r') as f:
        bp_dic = json.loads(f.read())

    print('[*] load %s breakpoint' % (len(bp_dic.keys())))

    img_base = pykd.module('escript').begin()

    print('[*] EScript.api image base : %s' % hex(img_base)[2:])

    b1 = pykd.setBp(toolbar_start+img_base, end_rec1)
    b2 = pykd.setBp(toolbar_ret+img_base, start_rec1)

    pykd.go()
