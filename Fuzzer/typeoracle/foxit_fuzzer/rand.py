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

import random

def P(p):
    return random.randint(0, 99) < p

def rand_integer():
    flag = random.randint(0, 10)
    if flag > 5:  # 5/11
        r = random.randint(0x0, 0xf)
    elif flag > 2:  # 3/11
        r = random.randint(0xf, 0xfff)
    elif flag > 0:  # 2/11
        r = random.randint(0xfff, 0xffff)
    else:  # 1/11
        r = random.randint(0xffff, 0x80000000)
    return str(r)


def rand_ascii(if_arr):
    def m1():
        a = random.randint(0x41, 0x5a)
        b = random.randint(0x61, 0x7a)
        return random.choice([a, b])

    def m2():
        return random.randint(0x20, 0x7e)

    def m3():
        return random.randint(0x0, 0xff)

    def choose():
        flg = random.randint(0, 2)
        if flg == 0:
            r = m1()
        elif flg == 1:
            r = m2()
        else:
            r = m3()
        return '\\\\x' + hex(r + 0x100)[3:]

    def level():
        if random.choice([0, 1]):
            r = random.randint(0x1000, 0x10000)
        else:
            r = random.randint(0x10, 0x1000)
        return '0x' + hex(r)[2:]

    result_string = ''
    if if_arr:
        if P(50):
            result_string = '''"\\\\xfe\\\\xff"''' + 'Array(%s).join("%s")' % (level(), choose())
        else:
            result_string = 'Array(%s).join("%s")' % (level(), choose())
    else:
        len_ = int(random.normalvariate(5, 5))
        if len_ < 0:
            len_ *= -1
        arr = [choose() for _ in range(len_)]
        if P(50):
            result_string = '''"\\\\xfe\\\\xff"''' + '"%s"' % ''.join(arr)
        else:
            result_string =  '"%s"' % ''.join(arr)

    return result_string


# pure unicode string
def rand_unicode(if_arr):
    def choose():
        return '\\\\u' + hex(random.randint(0x0, 0xffff) + 0x10000)[3:]

    def level():
        if random.choice([0, 1]):
            r = random.randint(0x1000, 0x8000)
        else:
            r = random.randint(0x10, 0x1000)
        return '0x' + hex(r)[2:]

    result_string = ''
    if if_arr:
        result_string = 'Array(%s).join("%s")' % (level(), choose())
    else:
        len_ = int(random.normalvariate(5, 5))
        if len_ < 0:
            len_ *= -1
        arr = [choose() for _ in range(len_)]
        result_string = '"%s"' % ''.join(arr)

    return result_string