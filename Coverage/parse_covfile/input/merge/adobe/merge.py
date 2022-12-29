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
import struct


def parse_module(lst):
    res = {}
    for ind, line in enumerate(lst):
        tmp = line.split(' ')[-1].strip()
        if tmp.startswith(r'DC\Reader'):
            indx = tmp.rindex('\\')
            name = tmp[indx+1:]
            res[ind] = name
    return res


def encode_data(offset_, size_):
    return str(offset_)+'_'+str(size_)


def decode_data(st):
    a, b = st.split('_')
    return int(a), int(b)


def parse_offset(eight):
    tmp = struct.unpack('<IHH', eight)
    r = encode_data(tmp[0], tmp[1])
    return (tmp[2], r)


def parse_file(fname):
    with open(fname, 'rb') as f:
        raw = f.read()
    for _ in range(2):
        tmp = raw.index(0xa)
        raw = raw[tmp+1:]
    tmp = raw.index(0xa)
    content = raw[:tmp]
    st = ''.join([chr(i) for i in content])
    count = int(st.split('count')[-1].strip())
    raw = raw[tmp+1:]

    arr = []
    for _ in range(count+1):
        tmp = raw.index(0xa)
        content = raw[:tmp]
        st = ''.join([chr(i) for i in content])
        arr.append(st)
        raw = raw[tmp+1:]
    res = parse_module(arr[1:])
    allowlst = sorted(list(res.keys()))

    tmp = raw.index(0xa)
    content = raw[:tmp]
    st = ''.join([chr(i) for i in content])
    # print(st)
    raw = raw[tmp+1:]
    bbklen = int(len(raw)/8)

    dic = {}
    for i in range(bbklen):
        tmp = raw[8*i:8*i+8]
        moduleid, offset = parse_offset(tmp)
        if moduleid in allowlst:
            if moduleid not in dic:
                dic[moduleid] = [offset]
            else:
                dic[moduleid].append(offset)
    count = 0
    newdic = {}
    for i in dic:
        newdic[res[i]] = set(dic[i])
        count += len(newdic[res[i]])
    #print('count: ',count)
    return newdic


def combine_dic(dic1,dic2):
    newdic = {}

    for i in dic1:
        if i not in dic2:
            newdic[i] = dic1[i]
            
    for i in dic2:
        if i not in dic1:
            newdic[i] = dic2[i]
    
    for i in dic1:
        if i in dic2:
            newdic[i] = dic1[i]|dic2[i]
    
    return newdic


def dump_dic(dic,dirpath):
    for key in dic:
        # print(key)
        fpath = os.path.join(dirpath, key)
        lst = sorted(list(dic[key]))
        nlst = []
        for i in lst:
            offset_, size_ = decode_data(i)
            tmp = struct.pack('<IH', offset_, size_)
            nlst.append(tmp)
        tmp = b''.join(nlst)
        with open(fpath, 'wb') as f:
            f.write(tmp)


# def load_from_save():
#     dic = {}
#     flst = os.listdir('combine')
#     for fname in flst:
#         fpath = os.path.join('combine', fname)
#         with open(fpath, 'rb') as f:
#             raw = f.read()
#         count = int(len(raw)/)
#         tmp = []
#         for i in range(count):
#             bt = raw[4*i:4*i+4]
#             val = struct.unpack('<I', bt)[0]
#             tmp.append(val)
#         dic[fname] = tmp
#         print(fname, len(tmp))
#     return dic


if __name__ == '__main__':
    # fname1 = sys.argv[1]
    # fname2 = sys.argv[2]
    # d1 = parse_file(fname1)
    # d2 = parse_file(fname2)
    # r = combine_dic(d1,d2)
    # dump_dic(r)
    d = parse_file('base.log')
    dirname = os.path.join('result','0')
    os.makedirs(dirname)
    dump_dic(d,dirname)
