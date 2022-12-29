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


def parse_all_file(data_fname):
    datadic = {}

    for fname in os.listdir(SAVE_DIR):
        dirpath = os.path.join(SAVE_DIR, fname)
        fpath = os.path.join(dirpath, data_fname+'.json')
        with open(fpath, 'r') as f:
            datadic[fname] = json.loads(f.read())

    # print('[+] load (%s) data complete' % data_fname)

    return datadic


def filter_ins(datadic):
    def check_valid(dic):
        if len(dic.keys()) == 1:
            k = list(dic.keys())[0]
            return 1.0, dic[k], k

        total = 0
        for k in dic:
            total += dic[k]
        mnum = min(int(total*0.9)+1, total)

        for k in dic:
            if dic[k] >= mnum:
                return dic[k]*1.0/total, dic[k], k
        return 0.0, 0, ''

    insdic = {}
    for apiname in datadic:
        for ins in datadic[apiname]:
            val = datadic[apiname][ins]

            if len(val[0]) == 0 or len(val[1]) == 0:
                st = 'invalid'
            else:
                st = '- %s + %s' % (','.join(sorted(val[0])),
                                    ','.join(sorted(val[1])))

            if ins not in insdic:
                insdic[ins] = {}
            if st not in insdic[ins]:
                insdic[ins][st] = 1
            else:
                insdic[ins][st] += 1

    res = []
    for ins in insdic:
        dic = insdic[ins]
        prob, cur, pattern = check_valid(dic)
        if prob != 0.0 and pattern != 'invalid':
            res.append((cur, ins, pattern, prob))

    res.sort(key=lambda x: x[0], reverse=True)

    #print('[+] filter instruction complete')

    return res


def find_equal(reslst, datadic):
    allowdic = {}
    for i in reslst:
        # count
        if i[0] >= 10:
            # ins - pattern
            allowdic[i[1]] = i[2]

    rdic = {}
    revinsdic = {}
    for apiname in datadic:
        nlst = []
        for ins in datadic[apiname]:
            if ins not in allowdic:
                continue
            val = datadic[apiname][ins]
            st = '- %s + %s' % (','.join(sorted(val[0])),
                                ','.join(sorted(val[1])))
            if st == allowdic[ins]:
                nlst.append(ins)
        for ins in nlst:
            if ins not in revinsdic:
                revinsdic[ins] = []
            revinsdic[ins].append(apiname)
        if len(nlst) > 1:
            for i in nlst:
                if i not in rdic:
                    rdic[i] = set([j for j in nlst if j!=i])
                else:
                    rdic[i] = set([j for j in nlst if j!=i]) &rdic[i]
    dic = {}
    num = 0
    for i in rdic:
        for j in rdic[i]:
            if i in rdic[j]:
                if i not in dic and j not in dic:
                    dic[i] = num
                    dic[j] = num
                    num += 1
                elif i in dic:
                    dic[j] = dic[i]
                elif j in dic:
                    dic[i] = dic[j]
    final = {}
    for i in dic:
        v = dic[i]
        if v not in final:
            final[v] = [i]
        else:
            final[v].append(i)
    
    nfinal = []
    for label in final:
        apilst = sorted(revinsdic[final[label][0]])
        inslst = sorted(final[label])
        count = len(apilst)
        nfinal.append((count,inslst,apilst))
    nfinal.sort(key=lambda x:x[0],reverse=True)

    return nfinal

def combine_setter(typename,classlst):
    def check_valid(curset,allowset,notallowset):
        if len(curset&allowset)>0 and len(curset&notallowset)==0:
            return True
        else:
            return False
    total = ['boolean','number','string']
    ctype = 'boolean' if typename == 'bool' else typename
    with open('setter.json','r') as f:
        dic = json.loads(f.read())
    allowset = dic[ctype]
    notallowset = []
    for key in dic:
        if key == ctype:
            continue
        if key in total:
            notallowset.extend(dic[key])
    allowset = set(['_'.join(i.split('.')) for i in allowset])
    notallowset = set(['_'.join(i.split('.')) for i in notallowset])
    result = []
    for item in classlst:
        if check_valid(set(item[2]),allowset,notallowset):
            result.append(item)
    return result

def combine_result(reslst,inslst):
    allowdic = {}
    for i in inslst:
        # count
        if i[0] >= 10:
            # ins - pattern
            allowdic[i[1]] = [i[2],i[3]]
    for item in reslst:
        tmp = [[i,allowdic[i][0],allowdic[i][1]] for i in item[1]]
        tmp.sort(key=lambda x:x[2],reverse=True)
        ntmp = []
        for i in tmp:
            if i[2]!=1.0:
                ntmp.append('%s*:%s'%(i[0],i[1]))
            else:
                ntmp.append('%s:%s'%(i[0],i[1]))
        print(item[0])
        print('\n'.join(ntmp))
    
def one_round(typename):
    datadic = parse_all_file(typename)
    res = filter_ins(datadic)
    final = find_equal(res,datadic)
    result = combine_setter(typename,final)
    print(typename+':')
    combine_result(result,res)
    print('\n')

if __name__ == '__main__':
    one_round('bool')
    one_round('number')
    one_round('string')