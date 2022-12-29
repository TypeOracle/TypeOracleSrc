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

SAVE_DIR = 'save'
INS_OUTPUT = 'ins'
DIC_OUTPUT = 'data'

global_h = ['this_resetForm','this_app_alert','this_app_enableToolButton']

def parse_all_data(data_fname):

    datadic = {}

    # 将所有结果全部收集到同一文件中
    for fname in os.listdir(SAVE_DIR):
        dirpath = os.path.join(SAVE_DIR, fname)
        fpath = os.path.join(dirpath, data_fname+'.json')
        with open(fpath, 'r') as f:
            datadic[fname] = json.loads(f.read())

    with open('%s_%s.json' % (DIC_OUTPUT, data_fname), 'w') as f:
        f.write(json.dumps(datadic))

    print('[+] load ( %s ) data complete ' % (data_fname))

    insdic = {}
    inscount = {}
    blacklst = []

    for apiname in datadic:
        for ins in datadic[apiname]:
            if ins in blacklst:
                continue
            value = datadic[apiname][ins]

            # 必须存在差异 不然怎么做diff
            if len(value[0]) == 0 or len(value[1]) == 0:
                blacklst.append(ins)
                continue

            # if len(value[0]) > 5 or len(value[1]) > 5:
            #     blacklst.append(ins)
            #     continue

            st = '- %s + %s' % (','.join(sorted(value[0])),
                                ','.join(sorted(value[1])))
            if ins not in insdic:
                insdic[ins] = st
                inscount[ins] = 1
            else:
                # 如果差分结果在不同API中不一致 也需要排除
                if insdic[ins] != st:
                    blacklst.append(ins)
                else:
                    inscount[ins] += 1

    order = []
    for key in insdic:
        if key in blacklst:
            continue
        # if inscount[key] >= 10:
        order.append([inscount[key], key, insdic[key]])

    order.sort(key=lambda x: x[0], reverse=True)

    h1 = [list(datadic[i].keys()) for i in global_h]

    tmp = []
    for i in order:
        if i[0] >= 5:
            tmp.append('%d %s %s' % (i[0], i[1], i[2]))
        else:
            tmp.append('%d %s' % (i[0], i[1]))
        flag = 0
        for ind,k in enumerate(h1):
            if i[1] in k:
                tmp[-1] = tmp[-1]+'+%d'%(ind)
                flag = 1
        if  i[0] >= 5 and flag ==1:
            print(tmp[-1])


    with open('%s_%s.txt' % (INS_OUTPUT, data_fname), 'w') as f:
        f.write('\n'.join(tmp))

    print('[+] filter ( %s ) instruction complete ' % (data_fname))


if __name__ == '__main__':
    parse_all_data('array')
    # parse_all_data('number')
    # parse_all_data('string')
