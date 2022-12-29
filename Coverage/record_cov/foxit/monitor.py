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
import sys
import time
import subprocess

import psutil
import pywinauto
import win32api

import random
import win32gui
import win32con

TOOL_PATH = r'C:\Users\wxy\Desktop\DynamoRIO\build32\bin32\drrun.exe'
ADOBE_PATH = r'"C:\Program Files (x86)\Foxit Software\Foxit PDF Reader\FoxitPDFReader.exe"'
CUR_PATH = r'"C:\Users\wxy\TypeOracle\Coverage\record_cov\foxit"'

TEST_DIR = 'test'
COV_DIR = 'cov'


class Monitor:

    def __init__(self, fileName, timeOut=120):
        self.status = 'init'
        self.fileName = fileName
        self.timeOut = timeOut
        self.find_foxit = False
        self.close_times = 0

    def log(self, info):
        # %Y-%m-%d
        t = time.strftime("%H:%M:%S", time.localtime())
        print(t + ' ' + info)

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

    # def run_windbg(self):
    #     cmd = '%s %s' % (ADOBE_PATH, os.path.join(CUR_PATH, 'test.pdf'))
    #     print(cmd)

    #     subprocess.Popen(cmd, shell=True)
    #     time.sleep(5)

    #     pid = self.getPidsByName('AcroRd32.exe')[0]
    #     self.pid = pid
    #     self.log('checkStart - pid:%d' % self.pid)

    #     cmd = 'cd %s&windbg.exe -p %d -c ".load pykd;!py -g %s"' % (
    #         WINDBG_PATH, pid, os.path.join(CUR_PATH, 'record.py')
    #     )
    #     print(cmd)

    #     subprocess.Popen(cmd, shell=True)
    #     time.sleep(5)

    #     self.app = pywinauto.Application().connect(process=self.pid)
    #     self.status = 'running'

    def clearDerived(self):
        # os.system(
        #     r'reg delete "HKEY_CURRENT_USER\Software\Adobe\Acrobat Reader\DC\Collab" /f')
        list_ = ['FoxitPDFReader.exe', 'WerFault.exe',
                 'splwow64.exe', 'OpenWith.exe', 'drrun.exe']
        for i in list_:
            self.closeProcess(i)

    def checkStart(self):
        pid_lst = self.getPidsByName('FoxitPDFReader.exe')
        if len(pid_lst) > 0:
            self.pid = pid_lst[0]
            self.app = pywinauto.Application().connect(process=self.pid)
            self.status = 'running'
            self.log('checkStart - pid:%d' % self.pid)
            return 1
        return 0

    def openPDF(self):
        # self.popup = 0
        fpath = os.path.join(TEST_DIR, self.fileName) if len(
            TEST_DIR) > 0 else self.fileName
        cmd = '%s -t drcov -logdir %s -- %s %s' % (
            TOOL_PATH, COV_DIR, ADOBE_PATH, os.path.join(CUR_PATH,fpath))
        subprocess.Popen(cmd,shell=True)
        print(cmd)
        ret = 0

        for _ in range(30):
            time.sleep(1)
            if psutil.cpu_percent(interval=1.0) < 20:
                self.log('pintool loaded complete')
                break

        for _ in range(15):
            time.sleep(1)
            if self.checkStart():
                ret = 1
                break
        return ret == 1

    def checkHalt(self):
        ret = 0
        if not self.app.is_process_running():
            ret = 1
            self.status = 'halt'
            self.log('Check - Halt')
        return ret

    def checkCrash(self):
        ret = 0
        list_ = self.getPidsByName('WerFault.exe')
        if len(list_) > 0:
            WerFault_pid = list_[0]
            WerFault_app = pywinauto.Application().connect(process=WerFault_pid)
            for win in WerFault_app.windows():
                w_text = win.window_text()
                if "Foxit" not in w_text:
                    self.closeProcess('WerFault.exe')
                    return ret
        

            ret = 1
            self.status = 'crash'
            self.log('Check - crash')
            self.closeProcess('WerFault.exe')
            if self.app.is_process_running():
                self.app.kill()
        return ret

    def checkPop(self):

        ret = 1
        self.closeProcess("VMwareHostOpen.exe")


        # for win in self.app.windows():
        #     if win.class_name() == 'AcrobatSDIWindow':
        #         win.set_focus()
        #         break

        win = self.app.top_window()
        cname = win.class_name()
        # self.log(cname)
        if cname != 'classFoxitReader':
            win.set_focus()
            self.log(cname)
            if cname == '#32770':
                if random.randint(1, 10) > 8:
                    pywinauto.keyboard.send_keys('{ENTER}')
                else:
                    pywinauto.keyboard.send_keys('%{F4}')
            else:
                pywinauto.keyboard.send_keys('%')
        elif win.window_text() == 'Foxit PDF Reader':
            self.status = 'finish'
            self.log('Check - close')
            try:
                win.close()
            except Exception as e:
                pass
        else:
            # self.log(cname)
            # pywinauto.keyboard.send_keys('%')
            ret = 0

        return ret

    def checkStatus(self, enter=0):
        if psutil.cpu_percent(interval=1.0) < 10:
            if not self.checkHalt():
                if not self.checkCrash():
                    if not self.checkPop():
                        if enter:
                            self.status = 'stop'
                            self.log('Check - stop')
                        else:
                            self.log('Check - low cpu usage')
                            time.sleep(1)
                            self.checkStatus(1)

    def checkMain(self):
        startTime = time.time()
        ret = 0

        for _ in range(self.timeOut // 2):
            time.sleep(1)
            self.checkStatus()
            if self.status != 'running':
                ret = 1
                break

        if not ret:
            self.status = 'hang'
            self.log('Check - hang')

        runTime = int(time.time() - startTime)
        self.log('End - running time: ' + str(runTime))

    # def writeResult(self):
    #     with open('runlog.txt', 'a') as f:
    #         f.write('%s %s %s\n' %
    #                 (self.fileName, self.status, str(self.popup)))
    #     return self.status

    def detect_window(self, hwnd, mouse):
        # print("detect_loginfo")
        windowtext = win32gui.GetWindowText(hwnd)
        # print("windowtext:{}".format(str(windowtext)))
        if "Foxit" in windowtext:
            self.find_foxit = True
            win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            win = self.app.top_window()
            cname = win.class_name()
            # self.log(cname)
            if cname != 'classFoxitReader':
                if not self.app.is_process_running():
                    return
                win.set_focus()
                self.log(cname)
                if cname == '#32770':
                    if random.randint(1, 10) > 5:
                        pywinauto.keyboard.send_keys('%{F4}')
                else:
                    pywinauto.keyboard.send_keys('%')
            time.sleep(0.5)
            pywinauto.keyboard.send_keys('{RIGHT}')
            self.log("send [RIGHT]")
            time.sleep(0.5)
            pywinauto.keyboard.send_keys('{ENTER}')
            self.log("send [ENTER]")


    def closeReader(self):
        if self.status == 'finish':
            for _ in range(10):
                time.sleep(1)
                if (not self.app.is_process_running()) or \
                        self.checkCrash():
                    break
        while self.app.is_process_running():
            self.log('Force quit')
            self.close_times += 1
            self.log("close times:{}".format(self.close_times))
            win32gui.EnumWindows(self.detect_window, 0)
            if self.close_times > 20:
                self.app.kill()
                self.close_times = 0
            time.sleep(1)
            if self.find_foxit == False:
                pywinauto.keyboard.send_keys('{ENTER}')
                self.log("send [ENTER]")
            self.find_foxit = False

        for _ in range(10):
            time.sleep(1)
            pid_lst = self.getPidsByName('drrun.exe')
            if len(pid_lst) == 0:
                break
            # todo check drrun

    def savePDF(self):
        if self.status != 'finish':
            if not os.path.exists('save'):
                os.makedirs('save')

            spath = os.path.join('save', self.status)
            if not os.path.exists(spath):
                os.makedirs(spath)

            newpath = os.path.join(spath, self.fileName)
            oripath = os.path.join(TEST_DIR, self.fileName) \
                if len(TEST_DIR) > 0 else self.fileName
            with open(oripath, 'r') as f:
                data = f.read()
            with open(newpath, 'w') as f:
                f.write(data)

            self.log('Save - %s - %s' % (self.status, self.fileName))

    def startUp(self):
        try:
            if self.openPDF():
                self.checkMain()
                self.closeReader()
        except Exception as e:
            self.status = 'error'
            self.log(str(e))
        try:
        	self.clearDerived()
        except Exception as e:
        	pass
        # self.savePDF()
        # self.writeResult()

        # return self.status


if __name__ == '__main__':
    m = Monitor('template.pdf')
    m.startUp()

    # tmp = os.listdir('test')
    # tmp.sort()
    # flag = 0
    # for fname in tmp:
    #     # if flag == 0:
    #     #     if fname == 'this_getUserUnitSize.pdf':
    #     #         flag = 1
    #     #     else:
    #     #         continue
    #     print(fname)
    #     m = Monitor(fname)
    #     m.startUp()
    # # m.writeResult()
