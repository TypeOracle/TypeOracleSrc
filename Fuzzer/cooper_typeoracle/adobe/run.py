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
import os
import monitor
import PdfSolution

TESTDIR = 'test'
SNUM = 2048
TNUM = 200000

def getname(elem):
    ret = 0
    try:
        ret = int(elem.split(".")[0])
    except Exception as e:
        print(str(e))
    return ret
    
class JSFuzz:

    def __init__(self):
        self.pdf_dirpath = 'PdfSamples'
        self.pdf_datapath = 'PdfData'
        self.pdf_outputpath = TESTDIR
        self.cooper_data = PdfSolution.pdf_cooper_data_prepare(self.pdf_dirpath, self.pdf_datapath)
        self.gen = generate.Generator()
        if not os.path.exists(TESTDIR):
            os.makedirs(TESTDIR)
        self.ind = 0
        self.curfname = ''

    def new_test(self):
        try:
            self.gen.clean_status()
            tmp = self.gen.create(SNUM)
            # jscode = 'try{spell.available}catch(e){};\n'+tmp+'\ncloseDoc(1);'
            jscode = tmp
            self.curfname = '%d.pdf' % self.ind
            PdfSolution.generate_new_test(self.pdf_dirpath, self.pdf_outputpath, self.cooper_data, jscode, self.curfname)
            self.ind += 1
        except Exception as e:
            print(e)
            # PdfSolution.generate_new_test(self.pdf_dirpath, self.pdf_outputpath, self.cooper_data, jscode, self.curfname)
            # self.ind += 1

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

    def runPDF(self):
        flst = os.listdir(TESTDIR)
        flst.sort(key=getname)
        for fname in flst:
            m = monitor.Monitor(fname)
            m.startUp()


if __name__ == '__main__':
    f = JSFuzz()
    f.startup()
