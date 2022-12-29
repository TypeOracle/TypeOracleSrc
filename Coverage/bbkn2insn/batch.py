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
import subprocess

IDA_PATH = r'"C:\Program Files\IDA 7.0\idat.exe"'
# CUR_PATH = r"C:\Users\wxy\Desktop\idabatch"
IDB_PATH = 'adobe_idb'

def main():

    flst = os.listdir(IDB_PATH)
    plst = [os.path.join(IDB_PATH, i) for i in flst]

    for i in plst:
        print(i)
        cmd = '%s -Llog\\%s.log -a -A -Sinscount.py %s' % (IDA_PATH, i, i)
        # cmd = '%s -a -A -Sinscount.py %s' % (IDA_PATH, i)
        # print(cmd)
        p = subprocess.Popen(cmd, shell=True)
        p.wait()


if __name__ == "__main__":
    main()
