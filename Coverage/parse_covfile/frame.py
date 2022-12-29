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
import time
import shutil

import merge

BASE_FILE = 'base.log'
INPUT_DIR = 'sample_data'
OUTPUT_DIR = 'sample_output'

def unzip(fpath):
    cmd = r'"C:\Program Files\7-Zip\7z.exe" '+'e -otmp %s' % fpath
    #cmd = '7za e -otmp %s' % fpath
    print(cmd)
    p = subprocess.Popen(cmd, shell=True)
    p.wait()


def rmtmp():
    shutil.rmtree('tmp')


def listtmp():
    flst = [os.path.join('tmp', i)
            for i in os.listdir('tmp') if i.endswith('.log')]
    nflst = [i for i in flst if os.path.getsize(i) > 0]
    nlst = [(int(os.path.getmtime(i)), i) for i in nflst]
    nlst.sort(key=lambda x: x[0])
    # for item in nlst:
    #     print(item[0], item[1])
    return nlst


def addtolog(timestamp, bbknum):
    with open('log.txt', 'a') as f:
        f.write('%d,%d' % (timestamp, bbknum)+'\n')


def countdic(dic):
    count = 0
    for k in dic:
        count += len(dic[k])
    return count


def handlezip(dirname):
    lst = os.listdir(dirname)
    len_ = len(lst)
    res = []
    for i in range(len_):
        fpath = os.path.join(dirname, 'cov%d.7z' % i)
        res.append(fpath)
    return res


if __name__ == '__main__':
    # fpath = os.path.join('db', 'cov%d.7z' % 0)
    # unzip(fpath)
    # print('finish')

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    dic = merge.parse_file(BASE_FILE)
    dirname = os.path.join(OUTPUT_DIR,'0')
    os.makedirs(dirname)
    merge.dump_dic(dic, dirname)

    total_size = 0
    # addtolog(0, 0)

    flag = 0
    basic_time = 0
    base = int(48*3600/100)
    recordtime = base

    flst = handlezip(INPUT_DIR)
    for zippath in flst:
        print('unzip '+zippath)
        unzip(zippath)

        lst = listtmp()
        for ind, item in enumerate(lst):
            timestamp, fpath = item
            if flag == 0:
                basic_time = timestamp
                flag = 1
            curtime = timestamp-basic_time
            print('%d/%d' % (ind+1, len(lst)), curtime, fpath)
            ndic = merge.parse_file(fpath)
            dic = merge.combine_dic(dic, ndic)
            # addtolog(timestamp, total_size)
            if curtime >= recordtime:
                print('[+] dumpinfo %d'%(int(recordtime/base)))
                dirname = os.path.join(OUTPUT_DIR,str(int(recordtime/base)))
                os.makedirs(dirname)
                merge.dump_dic(dic,dirname)
                recordtime += base
                if int(recordtime/base) == 100:
                    break


        print('delete tmp')
        rmtmp()

    # flst = [i for i in os.listdir('tmp') if i.endswith('.log')]
    # for i in flst[:10]:
    #     fpath = os.path.join('tmp', i)
    #     mtime = time.ctime(os.path.getmtime(fpath))
    #     ctime = time.ctime(os.path.getctime(fpath))
    #     print('m: %s, c: %s' % (mtime, ctime))

    # r = handlezip('db')
    # print('\n'.join(r))
