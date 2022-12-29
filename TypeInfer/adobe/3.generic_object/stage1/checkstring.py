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
import string

CUR_PATH = r'C:\Users\wxy\TypeOracle\Tools\TypeInfer\adobe\3.generic_object\stage1'

fnamelst = ['str_%d.json'%(i+1) for i in range(3)]

def func(fname):
    print('[+] '+fname)

    with open(os.path.join(CUR_PATH,fname),'r') as f:
        d = json.loads(f.read())

    lst = [(i[0]+0x23800000,i[1]) for i in d['EScript.api']]

    res = []
    for item in lst:
        tmp = idc.Name(item[0])
        if tmp.startswith('a'):
            val = GetString(item[0],-1,GetStringType(item[0]))
            res.append((val,item[1]))

    scope = string.letters

    def checkvalid(name):
        for c in name:
            if c not in scope:
                return 0
        return 1

    nres = [i for i in res if checkvalid(i[0])==1]
    final = {}
    for item in nres:
        s,t = item
        if s not in final:
            final[s] = t
        else:
            final[s] += t

    tmp = ['%s:%d'%(i,final[i]) for i in final]
    tmp.sort()

    # tmp = [i for i in tmp if i[0] in string.ascii_lowercase]

    print('\n'.join(tmp))
    print(len(tmp))

for i in fnamelst:
    func(i)