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
import monitor
# import handle
import time
import json
import parse
import mPDF

TEST_NUM = 8 # 6

class Template:

    def __init__(self):
        pass
        # with open('template.pdf', 'r') as f:
        #     raw = f.read()
        # rlst = raw.split('\n')
        # res = []
        # cur = []
        # for i in rlst:
        #     if i == '- - -':
        #         res.append(cur)
        #         cur = []
        #     else:
        #         cur.append(i)
        # res.append(cur)
        # self.content = ['\n'.join(i) for i in res]


    # def genstr(self, ind, apiname):
    #     arr = ['closeDoc(1)\ntry{\n%s()\n}catch(e){}\n',
    #            'arg=true\napp.toolbar\ntry{\n%s(arg)\n}catch(e){}\napp.toolbar\ncloseDoc(1)',
    #            'arg=false\napp.toolbar\ntry{\n%s(arg)\n}catch(e){}\napp.toolbar\ncloseDoc(1)',
    #            'arg=0x17\napp.toolbar\ntry{\n%s(arg)\n}catch(e){}\napp.toolbar\ncloseDoc(1)',
    #            'arg=0xb3\napp.toolbar\ntry{\n%s(arg)\n}catch(e){}\napp.toolbar\ncloseDoc(1)',
    #            'arg=Array(0xe).join("j")\napp.toolbar\ntry{\n%s(arg)\n}catch(e){}\napp.toolbar\ncloseDoc(1)',
    #            'arg=Array(0x18).join("Q")\napp.toolbar\ntry{\n%s(arg)\n}catch(e){}\napp.toolbar\ncloseDoc(1)']
    #     return arr[ind] % apiname

    def genstr(self, ind, apiname):
        arr = ['closeDoc(1)\ntry{\n%s(1)\n}catch(e){}\n',
        	   'arg=true\napp.toolbar\ntry{\n%s(arg)\n}catch(e){}\napp.toolbar\ncloseDoc(1)',
               'arg=false\napp.toolbar\ntry{\n%s(arg)\n}catch(e){}\napp.toolbar\ncloseDoc(1)',
               'arg=0x17\napp.toolbar\ntry{\n%s(arg)\n}catch(e){}\napp.toolbar\ncloseDoc(1)',
               'arg=0xb3\napp.toolbar\ntry{\n%s(arg)\n}catch(e){}\napp.toolbar\ncloseDoc(1)',
               'arg=Array(0xe).join("j")\napp.toolbar\ntry{\n%s(arg)\n}catch(e){}\napp.toolbar\ncloseDoc(1)',
               'arg=Array(0x18).join("Q")\napp.toolbar\ntry{\n%s(arg)\n}catch(e){}\napp.toolbar\ncloseDoc(1)',
               'arg=Array(0xd)\napp.toolbar\ntry{\n%s(arg)\n}catch(e){}\napp.toolbar\ncloseDoc(1)',
               'arg=Array(0x17)\napp.toolbar\ntry{\n%s(arg)\n}catch(e){}\napp.toolbar\ncloseDoc(1)']
        return arr[ind] % apiname

    # def genstr2(self, ind, apiname):
    #     arr = ['closeDoc(1)\ntry{\n%s\n}catch(e){}\n',
    #            'arg=true\napp.toolbar\ntry{\n%s=arg\n}catch(e){}\napp.toolbar\ncloseDoc(1)',
    #            'arg=false\napp.toolbar\ntry{\n%s=arg\n}catch(e){}\napp.toolbar\ncloseDoc(1)',
    #            'arg=0x17\napp.toolbar\ntry{\n%s=arg\n}catch(e){}\napp.toolbar\ncloseDoc(1)',
    #            'arg=0xb3\napp.toolbar\ntry{\n%s=arg\n}catch(e){}\napp.toolbar\ncloseDoc(1)',
    #            'arg=Array(0xe).join("j")\napp.toolbar\ntry{\n%s=arg\n}catch(e){}\napp.toolbar\ncloseDoc(1)',
    #            'arg=Array(0x18).join("Q")\napp.toolbar\ntry{\n%s=arg\n}catch(e){}\napp.toolbar\ncloseDoc(1)']
    #     return arr[ind] % apiname

    def genstr2(self, ind, apiname):
        arr = ['closeDoc(1)\ntry{\n%s=1\n}catch(e){}\n',
               'arg=true\napp.toolbar\ntry{\n%s=arg\n}catch(e){}\napp.toolbar\ncloseDoc(1)',
               'arg=false\napp.toolbar\ntry{\n%s=arg\n}catch(e){}\napp.toolbar\ncloseDoc(1)',
               'arg=0x17\napp.toolbar\ntry{\n%s=arg\n}catch(e){}\napp.toolbar\ncloseDoc(1)',
               'arg=0xb3\napp.toolbar\ntry{\n%s=arg\n}catch(e){}\napp.toolbar\ncloseDoc(1)',
               'arg=Array(0xe).join("j")\napp.toolbar\ntry{\n%s=arg\n}catch(e){}\napp.toolbar\ncloseDoc(1)',
               'arg=Array(0x18).join("Q")\napp.toolbar\ntry{\n%s=arg\n}catch(e){}\napp.toolbar\ncloseDoc(1)',               
               'arg=Array(0xd)\napp.toolbar\ntry{\n%s=arg\n}catch(e){}\napp.toolbar\ncloseDoc(1)',
               'arg=Array(0x17)\napp.toolbar\ntry{\n%s=arg\n}catch(e){}\napp.toolbar\ncloseDoc(1)']
        return arr[ind] % apiname

    def genpdf(self, apiname, flag=1):
        time.sleep(1)
        # l1 = '%s()' % apiname
        for i in range(TEST_NUM+1):
            if flag:
                ct = self.genstr(i, apiname)
            else:
                ct = self.genstr2(i, apiname)
            mPDF.make_pdf(ct,os.path.join('test','%d.pdf'%i))
            # c = [self.content[0], ct, self.content[1]]
            # with open(os.path.join('test', '%d.pdf' % i), 'w') as f:
            #     f.write('\n'.join(c))
        # l2 = '%s=arg' % apiname
        # c = [self.content[0], l2, self.content[1]]

        # with open('log.txt', 'a') as f:
        #     f.write(apiname+'\n')


def test_method(apiname):
    t = Template()
    t.genpdf(apiname)
    m = monitor.Monitor('1.out')
    st1 = m.start_up()
    if st1 == 'finish':
        m = monitor.Monitor('2.out')
        st2 = m.start_up()
        if st2 == 'finish':
        	# pass
            parse.one_round(apiname)


def test_setter(apiname):
    t = Template()
    t.genpdf(apiname, 0)
    m = monitor.Monitor('1.out')
    st1 = m.start_up()
    if st1 == 'finish':
        m = monitor.Monitor('2.out')
        st2 = m.start_up()
        if st2 == 'finish':
        	# pass
            parse.one_round(apiname)


if __name__ == '__main__':
    if not os.path.exists('test'):
        os.makedirs('test')
    # t = Template()
    # t.genpdf('this.app.alert')

    # test_method('this.gotoNamedDest')
    # test_setter('this.zoom')

    with open('funclst.txt', 'r') as f:
        raw = f.read()
    funclst = [i for i in raw.split('\n')]
    with open('setterlst.txt', 'r') as f:
        raw = f.read()
    setterlst = [i for i in raw.split('\n')]

    for apiname in funclst:
        print(apiname)
        tmp = '_'.join(apiname.split('.'))
        if os.path.exists(os.path.join('save', tmp)):
            print('skip')
            continue
        try:
            test_method(apiname)
        except Exception as e:
            with open('error.txt', 'a') as f:
                f.write(apiname+' '+str(e)+'\n')

    for apiname in setterlst:
        print(apiname)
        tmp = '_'.join(apiname.split('.'))
        if os.path.exists(os.path.join('save', tmp)):
            print('skip')
            continue
        try:
            test_setter(apiname)
        except Exception as e:
            with open('error.txt', 'a') as f:
                f.write(apiname+' '+str(e)+'\n')
