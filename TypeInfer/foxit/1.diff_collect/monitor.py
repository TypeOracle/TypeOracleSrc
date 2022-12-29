# -*- coding: utf-8 -*-

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
import time
import subprocess

import psutil
import pywinauto
import win32api

# 测试文件所在的文件夹
TEST_DIR = 'test'
TEST_NUM = 8
# 目前是7个文件 分别命名为0~7.pdf
FILE_LIST = [os.path.join(TEST_DIR, '%d.pdf') %
             i for i in range(1,TEST_NUM+1)]

# pin.exe路径
PIN_PATH = r'C:\Users\wxy\Desktop\pin-3.17\pin.exe'
# FoxitReader路径
FOXIT_PATH = r'"C:\Program Files (x86)\Foxit Software\Foxit Reader\FoxitReader.exe"'
CUR_PATH = r'C:\Users\wxy\TypeOracle\Tools\TypeInfer\foxit\1.diff_collect'

class Monitor:

    def __init__(self,output):
        # 设置初始状态
        self.status = 'init'
        self.output = output

    def log(self, info):
        # 输出信息时附上时间
        # %Y-%m-%d
        t = time.strftime("%H:%M:%S", time.localtime())
        print(t + ' ' + str(info))

    def getPidsByName(self, pname):
        return [p.info['pid']
                for p in psutil.process_iter(attrs=['pid', 'name'])
                if p.info['name'] == pname]

    def closeProcess(self, pname):
        list_ = [psutil.Process(i)
                 for i in self.getPidsByName(pname)]
        for p in list_:
            if p.is_running():
                p.kill()

    def clearDerived(self):
        list_ = ['FoxitReader.exe', 'pin.exe','WerFault.exe', 'splwow64.exe','OpenWith.exe']
        for i in list_:
            self.closeProcess(i)

    def run_pintool(self):
        command = '%s -t MyPinTool.dll -o %s -- %s %s' % (
            PIN_PATH, self.output, FOXIT_PATH, os.path.join(os.path.join(CUR_PATH,TEST_DIR), '0.pdf'))
        subprocess.Popen(command)
        self.log('start foxit with pintool')
        for _ in range(180):
            time.sleep(1)
            if psutil.cpu_percent(interval=1.0) < 20:
                self.log('foxit loaded complete')
                break

    def checkStart(self):
        pid_lst = self.getPidsByName('FoxitReader.exe')
        ret = 1 if len(pid_lst) == 1 else 0

        if ret:
            self.pid = pid_lst[0]
            self.app = pywinauto.Application().connect(process=self.pid)
            self.status = 'running'
            self.log('find applicaton - pid:%d' % (self.pid))
        else:
            self.log('fail to find target application')

        return ret

    def openPDF(self, fpath):
        # fpath = os.path.join(TEST_DIR, fname) \
        #     if len(TEST_DIR) > 0 else fname
        cmd = '%s %s' % (FOXIT_PATH,os.path.join(CUR_PATH,fpath))
        subprocess.Popen(cmd,shell=True)
        #win32api.ShellExecute(0, 'open', fpath, '', '', 1)
        self.status = 'running'

    def checkHalt(self):
        ret = 0
        lst = self.getPidsByName('WerFault.exe')
        if len(lst) > 0:
            ret = 1
            self.status = 'crash'
            self.log('check crash')
            self.closeProcess('WerFault.exe')
            return ret
        if not self.app.is_process_running():
            ret = 1
            self.status = 'halt'
            self.log('Check - Halt')
        return ret

    # def checkCrash(self):
    #     ret = 0
    #     list_ = self.getPidsByName('WerFault.exe')
    #     if len(list_) > 0:
    #         ret = 1
    #         self.status = 'crash'
    #         self.log('Check - crash')
    #         self.closeProcess('WerFault.exe')
    #         if self.app.is_process_running():
    #             self.app.kill()
    #     return ret

    # def checkClose(self):
    #     ret = 0
    #     for win in self.app.windows():
    #         if win.class_name() == 'classFoxitReader':
    #             if win.window_text() == 'Foxit Reader':
    #                 ret = 1
    #                 self.status = 'finish'
    #                 self.log('Check - close')
    #                 win.close()
    #             break
    #     return ret

    def checkPop(self, ifclose=0):
        ret = 1
        # try:
        # for win in self.app.windows():
        #     if win.class_name() == 'classFoxitReader':
        #         win.set_focus()
        #         break
        # for win in self.app.top_window():
        #     if win.class_name() == 'classFoxitReader':
        #         win.set_focus()
        #         break

        win = self.app.top_window()
        cname = win.class_name()

        if cname != 'classFoxitReader':
            win.set_focus()
            self.log(cname)
            pywinauto.keyboard.send_keys('%{F4}')
        elif win.window_text() == 'Foxit Reader':
            self.status = 'finish'
            self.log('Check - close')
            # 默认不关闭主程序 而是要打开下一个pdf文件
            if ifclose:
                try:
                    win.close()
                except Exception as e:
                    pass
        else:
            # 发送alt 主要为了处理popupmenu出现的右键菜单
            # pywinauto.keyboard.send_keys('%')
            ret = 0
        # if cname == '#32770':
        #     # and self.app.top_window().class_name()[:3] != 'AVL':
        #     pass
        # elif cname == '#32768':
        #     self.app.top_window().set_focus()
        #     ret = 0
        # except Exception as e:
        #    pass
        return ret

    def checkStatus(self, enter=0):
        if psutil.cpu_percent(interval=1.0) < 20:
            if not self.checkHalt():
                if not self.checkPop():
                    if enter:
                        self.status = 'stop'
                        self.log('Check - stop')
                    else:
                        self.log('Check - low cpu usage')
                        time.sleep(1)
                        self.checkStatus(1)

    def checkPerfile(self, remain):
        #startTime = time.time()
        ret = 0
        res = 0

        for i in range(remain, 90):
            res = i
            time.sleep(1)
            self.checkStatus()
            if self.status != 'running':
                ret = 1
                break

        if not ret:
            self.status = 'hang'
            self.log('Check - hang')

        self.log(str(res))
        return res

        #runTime = int(time.time() - startTime)
        #self.log('End - running time: ' + str(runTime))

    def checkMain(self):
        curtime = 0
        for fname in FILE_LIST:
            self.openPDF(fname)
            print(fname)
            curtime = self.checkPerfile(curtime)
            # if curtime >= 60:
            #     self.status = 'hang'
            #     self.log('Check - hang')
            if self.status != 'finish':
                self.log(self.status)
                break
            # time.sleep(1)
        if self.status == 'finish':
            self.log('close main window')
            self.checkPop(1)

    def closeReader(self):
        if self.status == 'finish':
            for _ in range(30):
                time.sleep(1)
                if not self.app.is_process_running():
                    self.log('application exit')
                    break

    # def savePDF(self):
    #     if self.status != 'finish':
    #         if not os.path.exists('save'):
    #             os.makedirs('save')

    #         spath = os.path.join('save', self.status)
    #         if not os.path.exists(spath):
    #             os.makedirs(spath)

    #         newpath = os.path.join(spath, self.fileName)
    #         oripath = os.path.join(TEST_DIR, self.fileName) \
    #             if len(TEST_DIR) > 0 else self.fileName
    #         with open(oripath, 'r') as f:
    #             data = f.read()
    #         with open(newpath, 'w') as f:
    #             f.write(data)

    #         self.log('Save - %s - %s' % (self.status, self.fileName))

    # def writeResult(self):
    #     msg = ','.join([str(i) for i in
    #                     [self.status]])
    #     with open('log.txt', 'a') as f:
    #         f.write(msg + '\n')
    #     return self.status

    def start_up(self):
        try:
            self.run_pintool()
            if self.checkStart():
                self.checkMain()
                if self.status == 'finish':
                    self.closeReader()
        except Exception as e:
            self.status = 'error'
            print(e)
            # self.log(e)
        # self.writeResult()
        self.clearDerived()

        return self.status
        # self.savePDF()


if __name__ == '__main__':
    m = Monitor(sys.argv[1])
    m.start_up()
