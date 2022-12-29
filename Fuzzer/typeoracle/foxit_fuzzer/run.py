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

import generate
import mPDF
import os
import monitor

TESTDIR = 'test'
SNUM = 256
TNUM = 20000

def getname(elem):
    ret = 0
    try:
        ret = int(elem.split(".")[0])
    except Exception as e:
        print(str(e))
    return ret

class JSFuzz:

    def __init__(self):
        self.gen = generate.Generator()
        if not os.path.exists(TESTDIR):
            os.makedirs(TESTDIR)
        self.ind = 0
        self.curfname = ''

    def new_test(self):
        self.gen.clean_status()
        tmp = self.gen.create(SNUM)
        tmp = 'try{spell.available}catch(e){};\n'+tmp+'\ncloseDoc(1);\n'
        fpath = os.path.join(TESTDIR, '%d.pdf' % self.ind)
        self.curfname = '%d.pdf' % self.ind
        self.ind += 1
        mPDF.make_pdf(tmp, fpath)

    def run_testcase(self):
        m = monitor.Monitor(self.curfname)
        m.startUp()
        m.writeResult()

    def startup(self):
        for _ in range(TNUM):
            self.new_test()
            print(self.curfname)
            try:
            	self.run_testcase()
            except Exception as e:
            	pass


if __name__ == '__main__':
    f = JSFuzz()
    f.startup()
    
