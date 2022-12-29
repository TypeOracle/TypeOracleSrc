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

# import os
# import json
# import random
# #from typing_extensions import Required


class Pattern:

    def __init__(self):
        self.root = ""  # root节点的id
        self.info = {}  # node的具体信息
        self.api = ""  # api的名称
        self.apitype = 0  # 0 method 1 setter
        self.prefer = []  # probe阶段的特殊结构
        self.ifopt = False  # 目前已经没用了

    def update_config(self, arg_info, ifopt=False):
        self.root = arg_info['root']
        self.info = arg_info['info']
        self.api = arg_info['api']
        self.apitype = arg_info['apitype']
        self.prefer = []
        self.ifopt = ifopt

    # def dump_pattern(self):
    #     # 暂时没有用到 Pattern只负责生成 不负责修改
    #     r = {'root': self.root,
    #          'info': self.info,
    #          'api': self.api,
    #          'apitype': self.apitype}
    #     return r

    def set_prefer(self, prefer):
        # prefer虽然设定为list 但一般只用来存在单个值
        def filter_complex(typelst):
            return [i for i in typelst if len(i) > 1]

        if len(prefer) == 0:
            self.prefer = []
        else:
            dep = {}
            # 寻找一条prefer中node到root的路
            # 把一路上的nodeid就标记为prefer
            # 记录复杂类型的父对象
            # 230->50->220 resetForm 则要把220和50都标记为prefer
            for i in self.info:
                if i == self.root:
                    continue
                # 因为root节点下的节点id一定在prefer中，没必要再追溯到root节点
                cur_node = self.info[i]
                if i.startswith('23') or i.startswith('22'):
                    tmp = filter_complex(
                        cur_node['req_type']+cur_node['opt_type'])
                    for t in tmp:
                        dep[t] = i
                elif i.startswith('5'):
                    tmp = filter_complex(cur_node['typelist'])
                    for t in tmp:
                        dep[t] = i

            oldlst = set(prefer[:])
            newlst = set(prefer[:])
            while True:
                tmp = [dep[i] for i in newlst if i in dep]
                newlst = newlst | set(tmp)
                if len(newlst-oldlst) == 0:
                    break
                else:
                    oldlst = set(list(newlst)[:])
                # 直到没有新的节点加入
            self.prefer = list(newlst)

    def handle_pattern(self, pattern, prefer=[]):
        # 关键接口
        self.update_config(pattern)
        self.set_prefer(prefer)
        return self.create()

    def handle_json(self, rule):
        req_key = rule['req_key']
        req_type = rule['req_type']
        opt_key = rule['opt_key']
        opt_type = rule['opt_type']

        arr = []

        for k, v in zip(req_key, req_type):
            tmp = self.dispatcher(v)
            arr.append('%s:%s' % (k, tmp))
        # 必填参数全部提供

        if not self.ifopt:
            # 大部分情况走这条路径
            for k, v in zip(opt_key, opt_type):
                if v in self.prefer:
                    tmp = self.dispatcher(v)
                    arr.append('%s:%s' % (k, tmp))
                # 可选参数如果在prefer中也需要提供
        else:
            for k, v in zip(opt_key, opt_type):
                tmp = self.dispatcher(v)
                arr.append('%s:%s' % (k, tmp))

        return '{%s}' % ','.join(arr)

    def handle_arr(self, rule):
        req_type = rule['req_type']
        opt_type = rule['opt_type']

        arr = []

        for t in req_type:
            tmp = self.dispatcher(t)
            arr.append(tmp)
        # 必填参数全部满足要求

        tmp = set(self.prefer) & set(opt_type)

        ind = 0
        for i in tmp:
            nind = len(opt_type) - 1 - opt_type[-1::-1].index(i)
            if nind > ind:
                ind = nind
        # 寻找列表中最后一个prefer中元素的位置
        # 例如 # 1 1 1, 1 50    nind = 2 - 1 - 0 = 1
        # 1 1 1 , 50 1 nind = 2 - 1 - 1 = 0

        if len(tmp) > 0:
            for i, t in enumerate(opt_type):
                tmp = self.dispatcher(t)
                arr.append(tmp)
                if i == ind:
                    break
            # 生成到最后一个prefer中的元素

        return '[%s]' % ','.join(arr)

    # def handle_conarr(self, rule):
    #     arrlen = random.randint(0, 7)
    #     curtype = rule['type']

    #     arr = []

    #     for _ in range(arrlen):
    #         tmp = self.dispatcher(curtype)
    #         arr.append(tmp)

    #     return '[%s]' % ','.join(arr)

    def handle_multi(self, rule):
        candidate = rule['typelist']
        tmp = list(set(candidate) & set(self.prefer))
        if len(tmp) > 0:
            # 一般情况下原始类型都在前面
            curtype = tmp[0]
        else:
            curtype = candidate[0]
        return self.dispatcher(curtype)

    def generate_value(self, typeid):
        if typeid == '0':
            return 'true'
        elif typeid == '1':
            return '0x1'
        elif typeid == '2':
            return '{}'
        elif typeid == '3':
            return '"a"'
        elif typeid == '4':
            return 'arg'
        elif typeid == '5':
            # value直接视为数字了
            return '0x1'
        else:
            # 理论上不会出现的情况
            return '0x1'

    def dispatcher(self, typeid):
        if typeid in self.info:
            # 如果记录在info中
            tmp = self.info[typeid]
            if typeid.startswith('23'):
                return self.handle_json(tmp)
            elif typeid.startswith('22'):
                return self.handle_arr(tmp)
            # elif typeid.startswith('21'):
            #     return self.handle_conarr(tmp)
            elif typeid.startswith('5'):
                return self.handle_multi(tmp)
            else:
                # 理论上不会出现这种情况 assert?
                return ''
        else:
            return self.generate_value(typeid)

    def create(self):
        tmp = self.dispatcher(self.root)
        if self.apitype == 0:
            # method 参数列表抽象为数组，所以这里要进行转换
            if tmp[0] == '[':
                tmp = tmp[1:-1]
            return '%s(%s)' % (self.api, tmp)
        else:
            return '%s=%s' % (self.api, tmp)


def create_object(argpattern, keylst):
    klst = [int(i[2:]) for i in argpattern['info'] if i.startswith('23')]
    if len(klst) > 0:
        klst.sort()
        curid = klst[-1]+1
    else:
        curid = 0
    nid = '23%d' % curid
    argpattern['info'][nid] = {
        'req_key': [], 'req_type': [],
        'opt_key': [], 'opt_type': [],
        'key_trace': [], 'key_rel': {},
        'pro_key': [], 'unpro_key': keylst[:]
    }
    return nid


def create_array(argpattern):
    klst = [int(i[2:]) for i in argpattern['info'] if i.startswith('22')]
    if len(klst) > 0:
        klst.sort()
        curid = klst[-1]+1
    else:
        curid = 0
    nid = '22%d' % curid
    argpattern['info'][nid] = {
        'req_type': [], 'opt_type': [], 'req_num': 0, 'is_pro': 0
    }
    return nid


def create_value(argpattern, valst):
    for ids in argpattern['info']:
        if ids.startswith('5'):
            if argpattern['info'][ids]['typelist'] == valst:
                # 在python3中可以直接比较数组 不知道python2可不可以
                return ids

    klst = [int(i[1:]) for i in argpattern['info'] if i.startswith('5')]
    if len(klst) > 0:
        klst.sort()
        curid = klst[-1]+1
    else:
        curid = 0
    nid = '5%d' % curid
    # 寻找下一个id

    argpattern['info'][nid] = {
        'typelist': valst[:]
    }
    return nid


def modify_argpattern(argpattern, oriid, newid):
    print('[+] find same node : %s == %s' % (oriid, newid))
    print('[+] replace : %s -> %s' % (oriid, newid))
    del argpattern['info'][oriid]
    for ids in argpattern['info']:
        curnode = argpattern['info'][ids]
        if ids.startswith('2'):
            for ind, i in enumerate(curnode['req_type']):
                if i == oriid:
                    curnode['req_type'][ind] = newid
            for ind, i in enumerate(curnode['opt_type']):
                if i == oriid:
                    curnode['opt_type'][ind] = newid
        elif ids.startswith('5'):
            for ind, i in enumerate(curnode['typelist']):
                if i == oriid:
                    curnode['typelist'][ind] = newid


def check_same_array(argpattern, curid):
    req_type = argpattern['info'][curid]['req_type']
    opt_type = argpattern['info'][curid]['opt_type']
    for ids in argpattern['info']:
        if curid == ids:
            continue
        if ids.startswith('22'):
            creq = argpattern['info'][ids]['req_type']
            copt = argpattern['info'][ids]['opt_type']
            if creq == req_type and copt == opt_type:
                modify_argpattern(argpattern, curid, ids)
                return


def check_same_object(argpattern, curid):
    req_type = argpattern['info'][curid]['req_type']
    opt_type = argpattern['info'][curid]['opt_type']
    req_key = argpattern['info'][curid]['req_key']
    opt_key = argpattern['info'][curid]['opt_key']
    for ids in argpattern['info']:
        if curid == ids:
            continue
        if ids.startswith('23'):
            creq = argpattern['info'][ids]['req_type']
            copt = argpattern['info'][ids]['opt_type']
            kreq = argpattern['info'][ids]['req_key']
            kopt = argpattern['info'][ids]['opt_key']
            if creq == req_type and copt == opt_type and kreq == req_key and kopt == opt_key:
                modify_argpattern(argpattern, curid, ids)
                return


if __name__ == '__main__':
    example = {'api': 'this.test', 'apitype': 0,
               'root': '230',
               'info': {
                   '230': {'req_key': ['cMsg', 'nIcon'],
                           'req_type': ['3', '1']}
               }}
    setter_example = {'api': 'this.setter', 'apitype': 1,
                      'root': '4', 'info': {}}
    argpattern0 = {'api': 'this.test', 'apitype': 0, 'root': '220',
                   'info': {'220': {'req_type': [], 'opt_type': []}}}
    argpattern = {'api': 'this.test', 'apitype': 0, 'root': '230',
                  'info': {'230': {
                      'req_key': [], 'req_type': [],
                      'opt_key': [], 'opt_type': [],
                      'key_trace': [], 'key_rel': {},
                      'pro_key': [], 'unpro_key': []}}}
    setter = {'api': 'setter', 'apitype': 1, 'root': '4',
              'info': {}}
    create_array(example)
    print(example)
    p = Pattern()
    print(p.handle_pattern(setter))
