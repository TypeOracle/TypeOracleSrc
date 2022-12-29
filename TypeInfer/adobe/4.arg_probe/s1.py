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


def shrink_content(content):
    for nodeid in content['info']:
        node = content['info'][nodeid]
        if nodeid.startswith('23'):
            alst = ['req_key', 'opt_key', 'req_type', 'opt_type']
            tmp = list(node.keys())
            for k in tmp:
                if k not in alst:
                    del node[k]
        elif nodeid.startswith('22'):
            alst = ['req_type', 'opt_type']
            tmp = list(node.keys())
            for k in tmp:
                if k not in alst:
                    del node[k]
        elif nodeid.startswith('23'):
            alst = ['typelist']
            tmp = list(node.keys())
            for k in tmp:
                if k not in alst:
                    del node[k]


def check_empty(content):
    rootid = content['root']
    node = content['info'][rootid]
    if len(node['req_type'])+len(node['opt_type']) == 0:
        return 0
    else:
        return 1


def fname2apiname(name):
    return '.'.join(name[:-5].split('_'))


if __name__ == '__main__':
    if not os.path.exists('data'):
        os.makedirs('data')

    flst1 = os.listdir('method_object')
    flst2 = os.listdir('method_array')
    flst = list(set(flst1+flst2))
    flst.sort()

    olst = []
    alst = []
    emptylst = []

    slst = []
    selst = []

    for fname in flst:
        print('current filename: '+fname)
        tmpresult = {}
        fpath1 = os.path.join('method_object', fname)
        fpath2 = os.path.join('method_array', fname)
        npath = os.path.join('data', fname)
        if not os.path.exists(fpath1):
            with open(fpath2, 'r') as f:
                tmpresult = json.loads(f.read())
        elif not os.path.exists(fpath2):
            with open(fpath1, 'r') as f:
                tmpresult = json.loads(f.read())
        else:
            with open(fpath1, 'r') as f:
                c1 = json.loads(f.read())
            with open(fpath2, 'r') as f:
                c2 = json.loads(f.read())
            f1 = check_empty(c1)
            f2 = check_empty(c2)
            if f1 == 0:  # empty object
                print('[array]')
                tmpresult = c2
                if f2 == 0:
                    emptylst.append(fname2apiname(fname))
                else:
                    alst.append(fname2apiname(fname))
            else:
                print('[gobject]')
                tmpresult = c1
                olst.append(fname2apiname(fname))
        # print(tmpresult)
        shrink_content(tmpresult)
        with open(npath, 'w') as f:
            f.write(json.dumps(tmpresult))

    olst.sort()
    alst.sort()
    emptylst.sort()

    flst3 = os.listdir('setter')
    for fname in flst3:
        print('current setter: '+fname)
        fpath = os.path.join('setter', fname)
        with open(fpath, 'r') as f:
            dic = json.loads(f.read())
        if dic['root'] == 5:
            selst.append(fname2apiname(fname))
        else:
            slst.append(fname2apiname(fname))
        npath = os.path.join('data', fname)
        with open(npath, 'w') as f:
            f.write(json.dumps(dic))

    slst.sort()
    selst.sort()

    tmp = 'object:\n'+'\n'.join(olst) + \
        '\n\narray:\n'+'\n'.join(alst) + \
        '\n\nempty:\n'+'\n'.join(emptylst) + \
        '\n\nsetter:\n'+'\n'.join(slst) + \
        '\n\nempty:\n'+'\n'.join(selst)

    with open('condition.txt', 'w') as f:
        f.write(tmp)
