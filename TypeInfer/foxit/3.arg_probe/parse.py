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

import json
import os
import time

tmp = os.stat('9.json')
timestamp = tmp.st_mtime

def loadjson(fname):
    with open(fname, 'r') as f:
        return json.loads(f.read())


def compare_value(valst1, valst2):
    def gen_dic(valst):
        dic = {}
        for i in valst:
            if i not in dic:
                dic[i] = 1
            else:
                dic[i] += 1
        return dic
    # print(valst1,valst2)
    dic1 = gen_dic(valst1)
    dic2 = gen_dic(valst2)
    # print(dic1,dic2)

    for i in dic2:
        if i not in dic1:
            dic1[i] = 0
    for i in dic1:
        if i not in dic2:
            dic2[i] = 0

    dec_set = []
    inc_set = []

    for key in dic1:
        a, b = dic1[key], dic2[key]
        if a > b:
            dec_set.append(key)
        elif a < b:
            inc_set.append(key)
    # print(dec_set,inc_set)
    return dec_set, inc_set


def classify_key(keylst):
    keydic = {}
    keyorder = []
    for i in keylst:
        if i not in keyorder:
            keyorder.append(i)
        if i not in keydic:
            keydic[i] = 1
        else:
            keydic[i] += 1
    res = []
    for i in keyorder:
        res.append([i, keydic[i]])
    return res


def check_type(dic1, dic2, typename):
    klst1 = dic1['key']
    klst2 = dic2['key']

    if klst1 != klst2:
        print('[!] in type: %s, different value leads to different keytrace' % typename)
        print(repr(klst1))
        print(repr(klst2))

        # tend to appear in Boolean/Number type
    # print(dic1['val'],dic2['val'])

    dec_set, inc_set = compare_value(dic1['val'], dic2['val'])

    flag = 0

    if typename == 'Boolean':
        if 0x1 in dec_set and 0x0 in inc_set:
            flag = 1
            #print('[+] Boolean match')
    elif typename == 'Number':
        if 0x2e in dec_set and 0x166 in inc_set:
            flag = 1
            #print('[+] Number match')
    elif typename == 'String':
        if 0x17 in dec_set and 0xb3 in inc_set:
            flag = 1
            #print('[+] String match')
    elif typename == 'Array':
        if 0x2e in dec_set and 0x166 in inc_set:
            flag = 1
            #print('[+] Array match')

    # if flag == 1:
    keyorder = classify_key(klst1)
    return flag, keyorder
    # print('\n'+typename+':')
    # print_keyorder(keyorder)


def handle_json(dic):
    #print('[?] Key for Object:')
    keyorder = classify_key(dic['key'])
    # print_keyorder(keyorder)
    return keyorder


def run_check():
    flag = 0
    for _ in range(10):
        tmp = os.stat('9.json')
        global timestamp
        curtime = tmp.st_mtime
        if curtime > timestamp:
            timestamp = curtime
            flag = 1
            break
        time.sleep(1)
        
    if flag == 0:
        print('[warning!!!!] time check failed, you may use the older data')

    a1, a2 = loadjson('1.json'), loadjson('2.json')
    a3, a4 = loadjson('3.json'), loadjson('4.json')
    a5, a6 = loadjson('5.json'), loadjson('6.json')
    a7, a8 = loadjson('7.json'), loadjson('8.json')
    a9 = loadjson('9.json')

    f1, l1 = check_type(a1, a2, 'Boolean')
    f2, l2 = check_type(a3, a4, 'Number')
    f3, l3 = check_type(a5, a6, 'String')
    f4, l4 = check_type(a7, a8, 'Array')
    l5 = handle_json(a9)

    keylst = [l1, l2, l3, l4, l5]
    reslst = []
    if f1:
        reslst.append(1)
    if f2:
        reslst.append(2)
    if f3:
        reslst.append(3)
    if f4:
        reslst.append(4)
    return keylst, reslst


def print_results(reslst, keylst):
    def print_keyorder(keyorder):
        for i, j in keyorder:
            print('%s %d' % (i, j))
    name = ['Boolean', 'Number', 'String', 'Array', 'Object']

    for i, j in enumerate(keylst):
        print('[*] %s' % name[i])
        print_keyorder(j)
        print('')

    for i in reslst:
        print('[+] %s type match !' % name[i-1])

# old <-> new


def compare_key(keypairs1, keypairs2, curkey=""):
    def trans(keypair):
        dic = {}
        for i in keypair:
            dic[i[0]] = i[1]
        return dic
    dic1 = trans(keypairs1)
    dic2 = trans(keypairs2)

    for i in dic1:
        if i not in dic2:
            dic2[i] = 0
    for i in dic2:
        if i not in dic1:
            dic1[i] = 0

    rlst = []
    for i in dic1:
        if i == curkey:
            continue
        if dic1[i] < dic2[i]:
            rlst.append(i)
    rlst = set(rlst)

    # 如果同时增加以下两组key则认为新增的key无效(错误处理)
    if 'name' in rlst and 'type' in rlst:
        rlst = rlst - set(['name', 'type'])
    if 'fileName' in rlst and 'targetName' in rlst and 'extMessage' in rlst:
        rlst = rlst - set(['fileName', 'targetName', 'extMessage'])

    if 'length' in rlst:
        rlst = rlst - set(['length'])

    res = []
    orderlst = [i[0] for i in keypairs2]
    # 回头按照原有的顺序进行排列
    for i in orderlst:
        if i in rlst:
            res.append(i)
    return res


def check_equal(keylst):
    # 所有keytrace完全相同
    base = keylst[0]
    for i in keylst[1:]:
        if i != base:
            return 0
    return 1


def check_dec(unpro_keylst, keylst):
    flag = 0
    # 只要存在有unprokey中的元素不见了，直接视为出现问题
    # 三个都出现问题
    for i in keylst:
        for j in unpro_keylst:
            if j not in i:
                flag += 1
                break
    if flag == 3:
        return 1
    else:
        return 0

# def check_error(key_trace):
#     def getkey(lst):
#         keylst = [i[0] for i in lst]
#         return set(keylst)
#     tmp = [getkey(i) for i in key_trace]

#     for i in ['fileName','targetName','extMessage']:
#         for j in tmp[:3]:
#             if i not in j:
#                 return 0
#         for j in tmp[3:]:
#             if i in j:
#                 return 0
#     return 1


def check_error(key_trace):
    tmp = [repr(i) for i in key_trace]
    if tmp[0] == tmp[1] and tmp[1] == tmp[2] and tmp[3] == tmp[4] and tmp[2] != tmp[3]:
        return 1
    else:
        return 0


def check_json_in_array(keylst):
    # 且object和其它明显不一样 则初步判断为'2'
    # 如果出现新key则认为是g_object
    # return flag,keylst
    # flag 0 无结果 1 其它object 2 keylst存在内容
    if check_error(keylst):
        newkeys = compare_key(keylst[0], keylst[-1])
        if len(newkeys) > 0:
            return 2, newkeys
        else:
            return 1, []
    else:
        return 0, []


if __name__ == '__main__':
    k, r = run_check()
    print_results(r, k)
