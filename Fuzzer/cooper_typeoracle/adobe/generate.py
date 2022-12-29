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


import pattern
import json
import os
import random

# TODO constant(pattern) blacklist whitelist

def getWeight(dic):
    def parselst(lst):
        # bool可选范围太小 直接当作没有参数
        return [i for i in lst if i != '0']
    if dic['apitype'] == 1:
        # setter统一为2
        return 2
    res = 1
    d = dic['info'][dic['root']]
    # 只统计root节点的参数信息
    if 'req_type' in d:
        res += len(parselst(d['req_type']))
        # TODO 复杂节点 增加权重
    if 'opt_type' in d and len(parselst(d['opt_type'])) > 0:
        res += 1
        # 可选参数权重统一为1
    return res


class Generator:

    def __init__(self):
        self.apidata = {}
        self.weightlst = []

        p1 = os.path.join('config','blacklist.txt')
        p2 = os.path.join('config','delist.txt')
        with open(p1,'r') as f:
            raw = f.read()
        blst = [i for i in raw.split('\n') if len(i)>0]
        with open(p2,'r') as f:
            raw = f.read()
        dlst = [i for i in raw.split('\n') if len(i)>0]
        blst = list(set(blst)-set(dlst))

        for fname in os.listdir('data'):
            fpath = os.path.join('data', fname)
            with open(fpath, 'r') as f:
                d = json.loads(f.read())
            apiname = d['api']
            if apiname in blst:
                continue
            # 忽略黑名单中的API
            p = pattern.Pattern(d)
            self.apidata[apiname] = p

            if apiname in dlst:
                w = 1
            else:
                w = getWeight(d)
            # dlst中的API会进行测试，但是减少测试的频率

            for _ in range(w):
                self.weightlst.append(apiname)

        random.shuffle(self.weightlst)

        self.alreadyapilist = []
        # 已经生成的API列表 (必须存在关联API)
        self.aleadyargdic = {}
        # {apiname:{type:valst}}

        self.relationship = {}
        with open('relationship.json', 'r') as f:
            raw = json.loads(f.read())
        nraw = {}
        for key in raw:
            if key in blst:
                continue
            tmp = list(set(raw[key])-set(key)-set(blst))
            if len(tmp) > 1:
                nraw[key] = sorted(tmp)
            # 之前生成relationship.json时忘记排除自身了
        self.relationship = nraw

        self.prefix = []
        # 存放function的生成
        self.content = []
        # 存在语句及变量的定义

        self.funcindex = 0
        # 记录需要的function的个数
        self.objindex = 0
        # api return value
        # 在prefix中设定初始值 防止函数运行出错

    def clean_status(self):
        self.alreadyapilist = []
        self.aleadyargdic = {}
        self.prefix = []
        self.content = []
        self.funcindex = 0
        self.objindex = 0

    def generate_without_complex(self):
        slen = random.randint(3, 5)
        res = []
        for _ in range(slen):
            curapi = random.choice(self.weightlst)
            self.apidata[curapi].clear_status()
            self.apidata[curapi].set_complex_flag(0)

            tmp = self.apidata[curapi].create()
            res.append(tmp)

            self.apidata[curapi].clear_status()

        return ';'.join(res)

    def generate_function(self):
        for ind in range(self.funcindex):
            tmp = 'f%d=function(){%s}' % (ind, self.generate_without_complex())
            self.prefix.append(tmp)

    def create(self, snum):
        for _ in range(snum):
            # select api
            # 只有存在关联关系的API才会加入其中
            curapi = ''
            while curapi not in self.apidata:
                if random.randint(1, 10) == 1 and len(self.alreadyapilist) > 0:
                    tmpapi = random.choice(self.alreadyapilist)
                    curapi = random.choice(self.relationship[tmpapi])
                    # print("little")
                    # 小概率选取与已生成API存在关联关系的API
                else:
                    curapi = random.choice(self.weightlst)
                    # print("big")
                    # 根据参数信息的复杂程度选取API

            # print("cur_api:%s"%curapi)
            # print(self.apidata)
            self.apidata[curapi].clear_status()
            # 清除状态

            if curapi in self.relationship:
                # 在参数生成时 用参数为API建立显式的关联关系
                apilst = self.relationship[curapi]
                # 获取所有存在关系的api
                argdic = {}
                for apiname in apilst:
                    if apiname in self.aleadyargdic:
                        # 如果该api已经生成
                        rdic = self.aleadyargdic[apiname]
                        for typeid in rdic:
                            if typeid not in argdic:
                                argdic[typeid] = rdic[typeid]
                            else:
                                argdic[typeid].extend(rdic[typeid])
                        # 将可复用的参数信息加入argdic中
                for typeid in argdic:
                    argdic[typeid] = set(argdic[typeid])
                # 去重(可选)
                if len(argdic.keys()) > 0:
                    self.apidata[curapi].update_oldvaldic(argdic)
                    # 将argdic用于参数生成

            self.apidata[curapi].set_valindex(self.funcindex)
            self.apidata[curapi].set_retindex(self.objindex)

            rdata = self.apidata[curapi].create()
            self.content.append(rdata)

            self.funcindex = self.apidata[curapi].get_valindex()
            self.objindex = self.apidata[curapi].get_retindex()

            if curapi in self.relationship:
                # 存在关联关系的API才会记录其已经使用的参数
                if curapi not in self.alreadyapilist:
                    self.alreadyapilist.append(curapi)
                    # 键入alreadyapilstt
                argdic = self.apidata[curapi].dump_curvaldic()
                if curapi not in self.aleadyargdic:
                    self.aleadyargdic[curapi] = argdic
                else:
                    for curid in argdic:
                        if curid not in self.aleadyargdic[curapi]:
                            self.aleadyargdic[curapi][curid] = argdic[curid]
                        else:
                            self.aleadyargdic[curapi][curid].extend(
                                argdic[curid])
                            self.aleadyargdic[curapi][curid] = list(
                                set(self.aleadyargdic[curapi][curid]))
                            # 去重

            self.apidata[curapi].clear_status()
            # 保险起见 再清楚一次

        # init by objindex
        for ind in range(self.objindex):
            tmp = 'var ret%d = 1'%ind
            self.prefix.append(tmp)
        
        self.generate_function()
        # generator function  by funcindex

        return '\n'.join(self.prefix)+'\n'+'\n'.join(self.content)

if __name__=='__main__':
    g = Generator()
    tmp = g.create(128)
    with open('js.txt','w') as f:
        f.write(tmp)

        
