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
# import label

# img_dic = {}


# def handle_module(lst):
#     if not os.path.exists('label.json'):
#         label.gen_label()

#     with open('label.json', 'r') as f:
#         label_dic = json.loads(f.read())

#     dic = {}

#     for line in lst:
#         img, low, high = line.split(':')
#         if img not in label_dic:
#             continue
#         dic[label_dic[img]] = [int(low, 16), int(high, 16)]

#     global img_dic
#     img_dic = dic


def handle_addr(addr,imgbase):
    return hex(addr-imgbase)[2:]
    # for key in img_dic:
    #     low, high = img_dic[key]
    #     if addr > low and addr < high:
    #         tmp = '%s_%s' % (key, hex(addr-low)[2:])
    #         return tmp
    # return ''


def parse_output(fname):

    # module = []
    trace = []

    with open(fname, 'r') as f:
        raw = f.read()

    iflag = 0

    cur_trace = []
    tmp = raw.split('\n')
    base = int(tmp[0],16)
    for i in tmp[1:]:
        if ' ' in i:
            cur_trace.append(i)
        # elif ':' in i:
        #     module.append(i)
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

    # handle_module(module)

    addr_cache = {}

    addr_value = {}

    result = []

    for strace in trace:

        for line in strace:

            label, value = line.split(' ')
            addr, ind = label.split('_')

            if addr not in addr_cache:
                addr_cache[addr] = handle_addr(int(addr, 16),base)

            newaddr = addr_cache[addr]
            if newaddr == '':
                continue
            newlabel = '%s_%s' % (newaddr, ind)

            if newlabel not in addr_value:
                addr_value[newlabel] = {}

            if value not in addr_value[newlabel]:
                addr_value[newlabel][value] = 1
            else:
                addr_value[newlabel][value] += 1

        result.append(addr_value)
        addr_value = {}

    return result, 1


def combine_dic(dic1, dic2):
    res = {}
    for key in dic1:
        if key in dic2:
            d1 = dic1[key]
            d2 = dic2[key]
            if set(d1.keys()) == set(d2.keys()):
                flag = 1
                for k in d1:
                    if d1[k] != d2[k]:
                        flag = 0
                        break
                if flag == 1:
                    res[key] = d1
    return res

def diff_dic(dic1, dic2):
    res = {}
    for key in dic1:
        if key in dic2:
            d1 = dic1[key]
            d2 = dic2[key]
            s1 = set(d1.keys())
            s2 = set(d2.keys())
            a1 = list(s1-s2)
            a2 = list(s2-s1)
            for k in d1:
                if k in d2:
                    if d1[k]>d2[k]:
                        a1.append(k)
                    elif d1[k]<d2[k]:
                        a2.append(k)
            if len(a1) > 0 and len(a2) > 0:
                res[key] = (sorted(a1), sorted(a2))
    return res


def batch_diff(diclst1, diclst2):
    res = []
    for d1, d2 in zip(diclst1, diclst2):
        tp = diff_dic(d1, d2)
        res.append(tp)
    return res


def dump_result(dic, fname):
    with open(fname, 'w') as f:
        f.write(json.dumps(dic))


def one_round(fname):
    if not os.path.exists('save'):
        os.makedirs('save')

    a1, code = parse_output('1.out')
    if code == 0:
        print('abnormal 1.out')
        with open('untestapi.txt', 'a') as f:
            f.write(fname+'\n')
        return
    print('1.out finish')
    a2, code = parse_output('2.out')
    if code == 0:
        print('abnormal 2.out')
        with open('untestapi.txt', 'a') as f:
            f.write(fname+'\n')
        return
    print('2.out finish')

    ndir = os.path.join('save', '_'.join(fname.split('.')))

    if not os.path.exists(ndir):
        os.makedirs(ndir)

    a3 = []
    # b3 = []
    for d1, d2 in zip(a1, a2):
        a3.append(combine_dic(d1, d2))
        # b3.append(combine_dic2(d1, d2))
    print('combine 1.out 2.out finish')

    a4 = batch_diff(a3[::2], a3[1::2])
    # b4 = batch_diff(b3[::2], b3[1::2])
    print('batch diff finish')

    #order = ['bool.json', 'number.json', 'string.json']
    # order = ['bool.json', 'array.json']
    order = ['bool.json', 'number.json', 'string.json', 'array.json']
    for i, j in zip(a4, [os.path.join(ndir, i) for i in order]):
        dump_result(i, j)
    # for i, j in zip(b4, [os.path.join(ndir, 'g'+i) for i in order]):
    #     dump_result(i, j)

    print('finish')


if __name__ == "__main__":
    one_round(sys.argv[1])
