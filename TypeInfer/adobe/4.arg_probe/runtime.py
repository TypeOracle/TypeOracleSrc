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
import mPDF
import monitor


class Template:

    def __init__(self):
        with open('jstemplate.js', 'r') as f:
            raw = f.read()
        rlst = [i.strip() for i in raw.split('\n') if len(i.strip()) > 0]
        self.lst1 = []
        self.lst2 = []
        flag = 0
        for i in rlst:
            if i == r'//---':
                flag = 1
                continue
            if flag == 0:
                self.lst1.append(i)
            else:
                self.lst2.append(i)
        self.pt = pattern.Pattern()

    def generate(self, pattern, prefer=[]):
        self.pt.handle_pattern(pattern, prefer)
        tmp = self.pt.create()
        lst = self.lst1 + [tmp] + self.lst2
        rawdata = '\n'.join(lst)
        mPDF.make_pdf(rawdata, 'test.pdf')

    # def generate2(self, pattern):
    #     self.pt.handle_pattern(pattern)
    #     self.pt.ifopt = True
    #     tmp = self.pt.create()
    #     lst = self.lst1 + [tmp] + self.lst2
    #     rawdata = '\n'.join(lst)
    #     mPDF.make_pdf(rawdata, 'test.pdf')


global_template = Template()
# 这个对象有点没有必要
# 直接在runtime.py时初始化时初始两个数组就行了


def init_runtime():
    m = monitor.Monitor()
    m.clean_status()
    flag = m.run_windbg()
    return m, flag


def close_runtime(m):
    m.one_file_end(1)
    # 0则表示不关闭程序? 那就直接不调用这个就行了
    m.clean_status()


def run_testcase(mt, arg_pattern, prefer=""):
    # generate testcase using pattern
    # run monitor using monitor.py
    global_template.generate(arg_pattern, prefer)

    mt.check_one_file('test.pdf')
    if mt.status != 'finish':
        print('<!> abormal behaviors')
        mt.clean_status()
        return 1
    else:
        # ret 0 means normal
        return 0

# def run_testcase2(mt, arg_pattern):
#     # generate testcase using pattern
#     # run monitor using monitor.py
#     global_template.generate2(arg_pattern)

#     mt.check_one_file('test.pdf')
#     if mt.status != 'finish':
#         print('<!> abormal behaviors')
#         mt.clean_status()
#         return 1
#     else:
#         # ret 0 means normal
#         return 0


if __name__ == '__main__':
    t = Template()
    example = {'api': 'this.app.alert', 'apitype': 0,
               'root': '230',
               'info': {
                   '230': {'req_key': ['cMsg'],
                           'req_type': ['3', '1']}
               }}
    t.generate(example)
