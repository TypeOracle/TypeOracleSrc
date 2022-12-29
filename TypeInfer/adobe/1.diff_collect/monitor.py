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

TEST_DIR = 'test'
TEST_NUM = 8

FILE_LIST = [os.path.join(TEST_DIR, '%d.pdf') %
             i for i in range(1, TEST_NUM+1)]

PIN_PATH = r'C:\Users\wxy\Desktop\pin-3.17\pin.exe'
ADOBE_PATH = r'"C:\Program Files (x86)\Adobe\Acrobat Reader DC\Reader\AcroRd32.exe"'
CUR_PATH = r'C:\Users\wxy\TypeOracle\Tools\TypeInfer\adobe\1.diff_collect'


class Monitor:

    def __init__(self, out_file):
        self.status = 'init'
        self.out_file = out_file

    def log(self, info):
        t = time.strftime("%H:%M:%S", time.localtime())
        print(t + ' ' + str(info))

    def get_pids(self, process):
        return [p.info['pid'] for p in psutil.process_iter(attrs=['pid', 'name'])
                if p.info['name'] == process]

    def close_process(self, process):
        lst = [psutil.Process(i) for i in self.get_pids(process)]
        for p in lst:
            if p.is_running():
                p.kill()

    def clean_status(self):
        os.system(
            r'reg delete "HKEY_CURRENT_USER\Software\Adobe\Acrobat Reader\DC\Collab" /f')
        lst = ['AcroRd32.exe', 'AdobeCollabSync.exe',
               'AdobeARM.exe', 'RdrCEF.exe', 'pin.exe', 'WerFault.exe', 'splwow64.exe','OpenWith.exe']
        # lst = ['AcroRd32.exe', 'pin.exe']
        for p in lst:
            self.close_process(p)

    def run_pin(self):
        cmd = '%s -t MyPinTool.dll -o %s -- %s %s' % (
            PIN_PATH, self.out_file, ADOBE_PATH, os.path.join(os.path.join(CUR_PATH,TEST_DIR), '0.pdf'))
        subprocess.Popen(cmd)
        self.log('start adobe reader with pintool')

        for _ in range(180):
            time.sleep(1)
            if psutil.cpu_percent(interval=1.0) < 20:
                self.log('pintool loaded complete')
                break

    def check_start(self):
        pid_lst = self.get_pids('AcroRd32.exe')
        ret = 1 if len(pid_lst) == 1 else 0

        if ret:
            self.pid = pid_lst[0]
            self.app = pywinauto.Application().connect(process=self.pid)
            self.status = 'running'
            self.log('find applicaton - pid:%d' % (self.pid))
        else:
            self.log('fail to find target application')

        return ret

    def open_file(self, fpath):
        cmd = '%s %s' % (ADOBE_PATH,os.path.join(CUR_PATH,fpath))
        subprocess.Popen(cmd,shell=True)
        #win32api.ShellExecute(0, 'open', fpath, '', '', 1)
        self.status = 'running'

    def check_halt(self):
        ret = 0
        lst = self.get_pids('WerFault.exe')
        if len(lst) > 0:
            ret = 1
            self.status = 'crash'
            self.log('check crash')
            self.close_process('WerFault.exe')
            return ret
        if not self.app.is_process_running():
            ret = 1
            self.status = 'halt'
            self.log('check halt')
        return ret

    def check_finish(self, ifclose=0):
        ret = 1

        for win in self.app.windows():
            if win.class_name() == 'AcrobatSDIWindow':
                win.set_focus()
                break

        win = self.app.top_window()
        cname = win.class_name()

        if cname != 'AcrobatSDIWindow':
            win.set_focus()
            self.log(cname)
            pywinauto.keyboard.send_keys('%{F4}')
        elif win.window_text() == 'Adobe Acrobat Reader DC':
            self.status = 'finish'
            self.log('check close')
            if ifclose:
                try:
                    win.close()
                except Exception as e:
                    pass
        else:
            ret = 0

        return ret

    def check_status(self, enter=0):
        if psutil.cpu_percent(interval=1.0) < 20:
            if not self.check_halt():
                if not self.check_finish():
                    if enter:
                        self.status = 'stop'
                        self.log('check stop')
                    else:
                        self.log('check - low cpu usage')
                        time.sleep(1)
                        self.check_status(1)

    def check_one_file(self, remain):
        ret = 0
        res = 0

        for i in range(remain, 90):
            res = i
            time.sleep(1)
            self.check_status()
            if self.status != 'running':
                ret = 1
                break

        if not ret:
            self.status = 'hang'
            self.log('check hang')

        self.log(str(res))
        return res

    def check_main(self):
        curtime = 0
        for fname in FILE_LIST:
            self.open_file(fname)
            print(fname)
            curtime = self.check_one_file(curtime)
            if self.status != 'finish':
                self.log(self.status)
                break
        if self.status == 'finish':
            self.log('close main window')
            self.check_finish(1)

    def wait_close(self):
        if self.status == 'finish':
            for _ in range(30):
                time.sleep(1)
                if not self.app.is_process_running():
                    self.log('application exit')
                    break

    def start_up(self):
        try:
            self.run_pin()
            if self.check_start():
                self.check_main()
                if self.status == 'finish':
                    self.wait_close()
        except Exception as e:
            self.status = 'error'
            print(e)

        self.clean_status()
        return self.status


if __name__ == "__main__":
    m = Monitor(sys.argv[1])
    m.start_up()
