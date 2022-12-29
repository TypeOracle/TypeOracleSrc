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
import idc
# import string

CUR_PATH = r'C:\Users\wxy\TypeOracle\Tools\TypeInfer\adobe\3.generic_object\stage2'

with open(os.path.join(CUR_PATH, 'bp.txt'), 'r') as f:
    raw = f.read()
rlst = [int(i.split('_')[1], 16) +
        0x23800000 for i in raw.split('\n') if len(i) > 0]

# res = []
# for item in lst:
#     tmp = idc.Name(item[0])
#     if tmp.startswith('a'):
#         val = GetString(item[0],-1,GetStringType(item[0]))
#         res.append((val,item[1]))


def handle_ins(addr):
    tmp = idc.print_operand(addr, 0)
    if tmp[0] == 'e' and len(tmp) == 3:
        return 'dd %s L1' % tmp
    elif '[' not in tmp:
        return ''
    else:
        i1 = tmp.index('[')
        i2 = tmp.index(']')
        ct = tmp[i1+1:i2]
        if '+' not in ct and '-' not in ct:
            if len(ct) == 3:
                return 'dd poi(%s) L1' % ct
            else:
                return ''
        offset = idc.get_operand_value(addr, 0)
        if '+' in ct:
            reg = ct.split('+')[0]
        else:
            reg = ct.split('-')[0]
        if offset > 0x100:
            offset = 0x100000000-offset
            l1 = hex(offset)
            l2 = l1[2:-1] if l1[-1] == 'L' else l1[2:]
            return 'dd poi(%s-%s) L1' % (reg, l2)
        else:
            l1 = hex(offset)
            l2 = l1[2:-1] if l1[-1] == 'L' else l1[2:]
            return 'dd poi(%s+%s) L1' % (reg, l2)


res = {}
for addr in rlst:
    tmp = idc.print_operand(addr, 0)
    val = handle_ins(addr)
    if len(val) == 0:
        print('skip %s %s' % (hex(addr), tmp))
    else:
        # print('%s %s : %s' % (hex(addr), tmp, val))
        key = hex(addr-0x23800000)[2:]
        if key[-1] == 'L':
            key = key[:-1]
        res[key] = val

with open(os.path.join(CUR_PATH,'bp.json'),'w') as f:
    f.write(json.dumps(res))
    # print(hex(addr),tmp)
    # res.append(tmp)

# t = []
# for item in res:
#     if '[' in item:
#         i1 = item.index('[')
#         i2 = item.index(']')
#         tmp = item[i1+1:i2]
#         t.append(tmp)
# t = sorted(list(set(t)))
# print('\n'.join(t))


# scope = string.letters

# def checkvalid(name):
#     for c in name:
#         if c not in scope:
#             return 0
#     return 1

# nres = [i for i in res if checkvalid(i[0])==1]
# final = {}
# for item in nres:
#     s,t = item
#     if s not in final:
#         final[s] = t
#     else:
#         final[s] += t

# tmp = ['%s:%d'%(i,final[i]) for i in final]
# tmp.sort()

# # tmp = [i for i in tmp if i[0] in string.ascii_lowercase]

# print('\n'.join(tmp))
# print(len(tmp))
