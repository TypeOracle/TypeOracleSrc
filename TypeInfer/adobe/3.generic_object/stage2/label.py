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
import json
import string

ADOBE_PATH = r'C:\Program Files (x86)\Adobe\Acrobat Reader DC\Reader\plug_ins'


def gen_label():
    flst = [i for i in os.listdir(ADOBE_PATH) if i.endswith('.api')]
    flst.sort()
    dic = {}
    for ind, item in enumerate(flst):
        dic[item] = string.ascii_letters[ind]
    with open('label.json', 'w') as f:
        f.write(json.dumps(dic))


if __name__ == '__main__':
    gen_label()
