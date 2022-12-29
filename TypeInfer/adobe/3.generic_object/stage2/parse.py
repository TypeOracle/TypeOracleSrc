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
import sys
import json
import label

img_dic = {}


def handle_module(lst):
    if not os.path.exists('label.json'):
        label.gen_label()

    with open('label.json', 'r') as f:
        label_dic = json.loads(f.read())

    dic = {}

    for line in lst:
        img, low, high = line.split(':')
        if img not in label_dic:
            continue
        dic[label_dic[img]] = [int(low, 16), int(high, 16)]

    global img_dic
    img_dic = dic


def handle_addr(addr):
    for key in img_dic:
        low, high = img_dic[key]
        if addr > low and addr < high:
            tmp = '%s_%s' % (key, hex(addr-low)[2:])
            return tmp
    return ''


def parse_output(fname):

    module = []
    trace = []

    with open(fname, 'r') as f:
        raw = f.read()

    iflag = 0

    cur_trace = []
    for i in raw.split('\n'):
        if ' ' in i:
            cur_trace.append(i)
        elif ':' in i:
            module.append(i)
        elif i == '[-!]':
            return [], 0
        elif i == '(+)':
            iflag = 0
        elif i == '[+]':
            iflag = 1
        elif i == '[-]':
            iflag = 0
        elif i == '(-)':
            if iflag == 0:
                trace.append(cur_trace)
                cur_trace = []
            else:
                return [], 0

    handle_module(module)

    addr_cache = {}

    addr_value = {}

    result = []

    for strace in trace:

        for line in strace:

            addr, value = line.split(' ')

            if addr not in addr_cache:
                addr_cache[addr] = handle_addr(int(addr, 16))

            newaddr = addr_cache[addr]
            if newaddr == '':
                continue

            if newaddr not in addr_value:
                addr_value[newaddr] = set()

            addr_value[newaddr].add(value)

        result.append(addr_value)
        addr_value = {}

    return result, 1

def filterdic(dic):
    allowlst = []
    blklst = []
    for key in dic:
        flag = 0
        for item in dic[key]:
            val = int(item,16)
            if val < 0x100000 or val > 0x80000000:
                flag = 1
                break
        if flag == 0:
            allowlst.append(key)
        else:
            blklst.append(key)
    return allowlst,blklst

if __name__ == "__main__":
    fname = ['1.out','2.out','3.out']
    alst = []
    blst = []
    for n in fname:
        r,flag = parse_output(n)
        if flag == 1:
            a,b = filterdic(r[0])
            alst.append(a)
            blst.append(b)
        else:
            print('err '+n)
    aset = set(alst[0])
    for i in alst[1:]:
        aset = aset & set(i)
    bset = set()
    for i in blst:
        bset = bset | set(i)
    final = sorted(list(aset-bset))
    print(len(final))
    with open('bp.txt','w') as f:
        f.write('\n'.join(final))