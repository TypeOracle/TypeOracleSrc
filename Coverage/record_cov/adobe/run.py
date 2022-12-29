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

import hashlib
import json
import os
import subprocess

import monitor
import random

TEST_DIR = 'test'

def getname(elem):
    ret = 0
    try:
        ret = int(elem.split(".")[0])
    except Exception as e:
        print(str(e))
    return ret

class JSFuzz:

    def __init__(self):
        self.cur_file = ''
        if not os.path.exists(TEST_DIR):
            os.mkdir(TEST_DIR)


    def zip_file(self, count):
        cmd = r'"C:\Program Files\7-Zip\7z.exe" a db/cov%d cov' % count
        p = subprocess.Popen(cmd)
        p.wait()
        for i in os.listdir('cov'):
            fpath = os.path.join('cov', i)
            if os.path.exists(fpath):
                os.remove(fpath)

    def runPDF(self):
        count = 0
        flst = os.listdir(TEST_DIR)
        flst.sort(key=getname)
        i = 0
        for fname in flst:
            m = monitor.Monitor(fname)
            m.startUp()
            if (i+1) % 100 == 0:
                self.zip_file(count)
                count += 1
            i += 1

if __name__ == '__main__':
    if not os.path.exists('cov'):
        os.makedirs('cov')
    if not os.path.exists('db'):
        os.makedirs('db')
    f = JSFuzz()
    f.runPDF()
