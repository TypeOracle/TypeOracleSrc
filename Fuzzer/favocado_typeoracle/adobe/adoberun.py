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

import amonitor
import generate
import os
import subprocess

DEFAULT = 1
TEST_NUM = 100000


def getname(elem):
    ret = 0
    try:
        ret = int(elem.split(".")[0])
    except Exception as e:
        print(str(e))
    return ret

class JSFuzz:
    def __init__(self):
        self.totalcase = 0

    def new_test(self):
        generate.generate_js(DEFAULT)
        generate.combine_pdf()
        self.totalcase += DEFAULT

    def startup(self):
        for i in range(TEST_NUM):
            if i == self.totalcase:
                self.new_test()
            m = amonitor.Monitor('%d.pdf' % i)
            m.startUp()
            m.writeResult()

    def zip_file(self, count):
        cmd = r'"C:\Program Files\7-Zip\7z.exe" a db/cov%d cov' % count
        p = subprocess.Popen(cmd)
        p.wait()
        for i in os.listdir('cov'):
            fpath = os.path.join('cov', i)
            if os.path.exists(fpath):
                os.remove(fpath)

    def runPDF(self):
        flst = os.listdir(TESTDIR)
        flst.sort(key=getname)
        for fname in flst:
            m = monitor.Monitor(fname)
            m.startUp()
            m.writeResult()



if __name__ == '__main__':
    f = JSFuzz()
    f.startup()
    # f.runPDF()
