# coding=utf-8

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

import random
import json
import rand
import os

fp1 = os.path.join('config','strlst.json')
fp2 = os.path.join('config','objlst.txt')
with open(fp1,'r') as f:
    l1 = json.loads(f.read().replace('\\\\', '\\'))
interesting_str = ['''"a" + String.fromCharCode(0x4141)''']
interesting_str.extend(l1)
interesting_number = ['-1', '0x7fffffff', '0xffffffff', '256', '255', '127', '128']
with open(fp2,'r') as f:
    raw = f.read()
l2 = [i for i in raw.split('\n') if len(i)>0]

constant_dic = {
    '1': interesting_number, 
    '2': l2,
    '3': interesting_str
} #1number,  2 obj, 3 string
#print(constant_dic)


def rand_bool():
    return random.choice(['true', 'false'])


def rand_num():
    if rand.P(50):
        c = '' if rand.P(33) else '-' #1/3
        return '%s%s.%s' % (c, rand.rand_integer(), ''.join(reversed(rand.rand_integer())))
    else:
        c = '' if rand.P(33) else '-' #1/3
        return '%s%s' % (c, rand.rand_integer())


def rand_obj():
    return random.choice([r'{}', r'[]'])


def rand_str():
    tmp = random.randint(0, 9)
    if tmp > 5:
        return rand.rand_ascii(0)
    elif tmp > 2:
        return rand.rand_ascii(1)
    elif tmp > 0:
        return rand.rand_unicode(0)
    else:
        return rand.rand_unicode(1)


randfunc_dic = {
    '0': rand_bool,
    '1': rand_num,
    '2': rand_obj,
    '3': rand_str
}


def rand_dispatcher(typeid):
    if rand.P(1): # 10% random value
        typeid = '5'
    if typeid == '5' or typeid == 5: # some setter is 5
        ntypeid = random.choice(['0', '1', '2', '3'])
    else:
        ntypeid = typeid
    # print("typeid:%s"%ntypeid)

    if ntypeid in randfunc_dic:
        return randfunc_dic[ntypeid]()
    else:
        # 理论上不应该出现
        return '1'


class Pattern:

    def __init__(self, arg_pattern):
        self.arg_pattern = arg_pattern
        self.old_valdic = {}
        self.cur_valdic = {}
        self.valindex = 0
        self.prefix_content = []
        self.complex_flag = 1
        self.retindex = 0

    def clear_status(self):
        self.valindex = 0
        self.old_valdic = {}
        self.cur_valdic = {}
        self.prefix_content = []
        self.complex_flag = 1
        self.retindex = 0

    def set_complex_flag(self, flag):
        self.complex_flag = flag

    def update_oldvaldic(self, dic):
        self.old_valdic = dic

    def dump_curvaldic(self):
        res = {}
        for typeid in self.cur_valdic:
            res[typeid] = list(set(self.cur_valdic[typeid]))
        return res

    def set_valindex(self, ind):
        self.valindex = ind

    def get_valindex(self):
        return self.valindex

    def set_retindex(self, ind):
        self.retindex = ind

    def get_retindex(self):
        return self.retindex

    def dispatcher(self, typeid):
        if typeid in self.arg_pattern['info']:
            return self.complextype_dispatcher(typeid, self.complex_flag)
        else:
            return self.basictype_dispatcher(typeid, self.complex_flag)

    def basictype_objarg(self, typeid):
        cur_val = self.basictype_dispatcher(typeid, 0)
        tmp1 = 'var fs%d = function(){f%d();return %s;}' % (
            self.valindex, self.valindex, cur_val)
        tmp2 = 'var os%d = {};' % (self.valindex)
        for i in range(random.randint(0, 3)):
            tmp2 = tmp2 + 'os%d[%s] = %s;' % (self.valindex, self.basictype_dispatcher('5', 0), self.basictype_dispatcher('5', 0))
        if typeid == '3':
            tmp2 += 'os%d.toString = fs%d' % (self.valindex, self.valindex)
        else:
            tmp2 += 'os%d.valueOf = fs%d' % (self.valindex, self.valindex)
        return 'os%d' % self.valindex, tmp1+'\n'+tmp2

    def basictype_dispatcher(self, typeid, complex_flag=1):
        if rand.P(10) and typeid in constant_dic: # 10% contant object or string
            return random.choice(constant_dic[typeid])
        elif complex_flag and rand.P(10) and typeid in self.old_valdic and len(self.old_valdic[typeid])>0: # 10% already exist value
            return random.choice(list(self.old_valdic[typeid]))
        elif complex_flag and rand.P(10):  # 10% create new object value
            val, prefix = self.basictype_objarg(typeid)
            self.prefix_content.append(prefix)
            self.valindex += 1
            return val
        else:
            val = rand_dispatcher(typeid)
            if typeid not in self.cur_valdic:
                self.cur_valdic[typeid] = []
            self.cur_valdic[typeid].append(typeid)
            return val

    def handle_json(self, rule):
        req_key = rule['req_key']
        req_type = rule['req_type']
        opt_key = rule['opt_key']
        opt_type = rule['opt_type']

        arr = []

        rec = []

        for k, v in zip(req_key, req_type):
            tmp = self.dispatcher(v)
            arr.append('%s:%s' % (k, tmp))
            if v in ['0', '1', '3']:
                rec.append([k, v, tmp])

        for k, v in zip(opt_key, opt_type):
            if random.randint(0, 3):
                tmp = self.dispatcher(v)
                arr.append('%s:%s' % (k, tmp))
                if v in ['0', '1', '3']:
                    rec.append([k, v, tmp])

        return '{%s}' % ','.join(arr), rec

    def handle_arr(self, rule):
        req_type = rule['req_type']
        opt_type = rule['opt_type']

        arr = []

        curind = 0 #arg index
        rec = []

        for t in req_type:
            tmp = self.dispatcher(t)
            arr.append(tmp)
            if t in ['0', '1', '3']:
                rec.append([curind, t, tmp])
            curind += 1

        for t in opt_type:
            if random.randint(0, 3):
                tmp = self.dispatcher(t)
                arr.append(tmp)
                if t in ['0', '1', '3']:
                    rec.append([curind, t, tmp])
            else:
                break
            curind += 1
        # print(arr)
        return '[%s]' % ','.join(arr), rec

    def handle_multi(self, rule):
        candidate = rule['typelist']
        curtype = random.choice(candidate)

        return self.dispatcher(curtype)

    def complextype_objarg(self, typeid, content, recpair):
        cur_val = self.basictype_dispatcher(recpair[1], 0)
        tmp1 = 'var fs%d = function(){f%d();return %s;}' % (
            self.valindex, self.valindex, cur_val)
        tmp2 = 'var os%d = %s;' % (self.valindex, content)
        if typeid.startswith('22'):
            tmp3 = 'Object.defineProperties(os%d, {%d: {get: fs%d}});' % (
                self.valindex, recpair[0], self.valindex
            )
            tmp2 += '\n'+tmp3
        elif typeid.startswith('23'):
            tmp3 = 'Object.defineProperties(os%d, {%s: {get: fs%d}});' % (
                self.valindex, recpair[0], self.valindex
            )
            tmp2 += '\n'+tmp3
        return 'os%d' % self.valindex, tmp1+'\n'+tmp2

    def complextype_dispatcher(self, typeid, complex_flag=1):
        # print(complex_flag)
        info = self.arg_pattern['info']

        if typeid not in info:
            return '[]'

        rule = info[typeid]

        res = ''
        rec = [] # triple: 0:index(json key), 1:value type, 2:real value

        if typeid.startswith('5'):
            return self.handle_multi(rule)

        if typeid.startswith('23'):
            res, rec = self.handle_json(rule)
        elif typeid.startswith('22'):
            res, rec = self.handle_arr(rule)
        else:
            return '[]'

        if complex_flag and len(rec) > 0 and rand.P(10):
            pos, ctype, cval = random.choice(rec)
            if ctype in self.cur_valdic:
                self.cur_valdic[ctype] = list(
                    set(self.cur_valdic[ctype])-set([cval]))
            val, prefix = self.complextype_objarg(typeid, res, [pos, ctype])
            self.prefix_content.append(prefix)
            self.valindex += 1
            return val
        else:
            return res

    def create(self):
        res = ''
        tmp = self.dispatcher(self.arg_pattern['root'])
        if self.arg_pattern['apitype'] == 0:
            if tmp[0] == '[':
                tmp = tmp[1:-1]
            res = '%s(%s)' % (self.arg_pattern['api'], tmp)
            if self.complex_flag and 'ret_type' in self.arg_pattern and rand.P(25):
                res = 'ret%d=%s' % (self.retindex, res)
                self.cur_valdic[self.arg_pattern['ret_type']
                                ] = 'ret%d' % self.retindex
                self.retindex += 1
        else:
            res = '%s=%s' % (self.arg_pattern['api'], tmp) # setter 
        if len(self.prefix_content) > 0:
            res = ';'.join(self.prefix_content)+';'+'try{%s}catch(e){}'%res
        else:
            res = 'try{%s}catch(e){}'%res
        return res


if __name__ == '__main__':
    # TODO 设置是否接收返回值
    with open('this_stampAPFromPage.json', 'r') as f:
        dic = json.loads(f.read())
    p = Pattern(dic)
    res = []
    for _ in range(50):
        p.set_complex_flag(1)
        r = p.create()
        res.append(r)
        print(p.get_valindex())
        print(p.dump_curvaldic())
        print('')
        p.clear_status()
    with open('result.txt', 'w') as f:
        f.write('\n\n'.join(res))
