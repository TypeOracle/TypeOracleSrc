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

WINDBG_PATH = r'C:\Program Files (x86)\Windows Kits\8.1\Debuggers\x64'
ADOBE_PATH = r'C:\"Program Files (x86)"\Adobe\"Acrobat Reader DC"\Reader\AcroRd32.exe'
CUR_PATH = r'C:\Users\wxy\TypeOracle\Tools\TypeInfer\adobe\4.arg_probe'


class Monitor:

    def __init__(self):
        self.status = 'init'

    def log(self, info):
        t = time.strftime("%H:%M:%S", time.localtime())
        print(t + ' ' + str(info))

    def get_pids(self, process):
        # 存在延时 可能会出问题
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
               'AdobeARM.exe', 'RdrCEF.exe',
               'WerFault.exe', 'splwow64.exe',
               'windbg.exe', 'OpenWith.exe']
        # lst = ['AcroRd32.exe', 'pin.exe']
        self.log('<*> clean remained process')
        for p in lst:
            try:
                self.close_process(p)
            except Exception as e:
                pass

    # def run_pin(self):
    #     cmd = '%s -t MyPinTool.dll -o %s -- %s' % (
    #         PIN_PATH, self.out_file, ADOBE_PATH)
    #     subprocess.Popen(cmd)
    #     self.log('start adobe reader with pintool')

    #     for _ in range(30):
    #         time.sleep(1)
    #         if psutil.cpu_percent(interval=1.0) < 10:
    #             self.log('pintool loaded complete')
    #             break

    def run_windbg(self):
        cmd = '%s %s' % (ADOBE_PATH, os.path.join(CUR_PATH, 'init.pdf'))
        print('<+> run the target program:'+cmd)
        subprocess.Popen(cmd, shell=True)
        time.sleep(3)
        # 打开init.pdf 载入EScript模块

        # TODO 循环check start?
        if self.check_start():

            # pid = self.getPidsByName('AcroRd32.exe')[0]
            # self.pid = pid
            # self.log('checkStart - pid:%d' % self.pid)

            cmd = 'cd %s&windbg.exe -p %d -c ".load pykd;!py -g %s"' % (
                WINDBG_PATH, self.pid, os.path.join(CUR_PATH, 'record.py')
            )
            print('<+> start Windbg:'+cmd)
            # TODO 似乎没有考虑windbg未能正常启动的情况
            subprocess.Popen(cmd, shell=True)
            time.sleep(5)
            # 启动windbg 载入record.py脚本
            return 0

        return 1

        # self.app = pywinauto.Application().connect(process=self.pid)
        # self.status = 'running'

    def check_start(self):
        pid_lst = self.get_pids('AcroRd32.exe')
        ret = 1 if len(pid_lst) == 1 else 0

        if ret:
            self.pid = pid_lst[0]
            self.app = pywinauto.Application().connect(process=self.pid)
            self.status = 'running'
            self.log('<+> find target programs, id:%d' % (self.pid))
        else:
            self.log('<!> failed to find the target programs')

        return ret

    def open_file(self, fpath):
        # 这么看来还是要将目标程序设为默认程序
        win32api.ShellExecute(0, 'open', fpath, '', '', 1)
        self.status = 'running'

    def check_halt(self):
        ret = 0
        lst = self.get_pids('WerFault.exe')
        if len(lst) > 0:
            ret = 1
            self.status = 'crash'
            self.log('<+> crash check')
            self.close_process('WerFault.exe')
            return ret
        if not self.app.is_process_running():
            ret = 1
            self.status = 'halt'
            self.log('<+> halt check')
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
            # if cname == '#32770':
            if cname == '#32768':
                pywinauto.keyboard.send_keys('%{a}')
                # 只要alt就行 但可能导致选择到菜单 导致下个文档无法正常打开
            else:
                pywinauto.keyboard.send_keys('%{F4}')
        elif win.window_text() == 'Adobe Acrobat Reader DC':
            self.status = 'finish'
            self.log('<+> finish check')
            # for win in self.app.windows():
            #     if win.class_name() == 'AcrobatSDIWindow':
            #         win.set_focus()
            #         break
            if ifclose:
                try:
                    win.close()
                except Exception as e:
                    pass
        else:
            ret = 0

        return ret

    def check_status(self, enter=0):
        if psutil.cpu_percent(interval=1.0) < 10:
            if not self.check_halt():
                if not self.check_finish():
                    if enter:
                        self.status = 'stop'
                        self.log('<+> stop checked')
                    else:
                        self.log('<+> low cpu usage')
                        time.sleep(1)
                        self.check_status(1)

    def check_one_file(self, fname):
        self.open_file(fname)
        # time.sleep(1)
        ret = 0
        for _ in range(30):
            time.sleep(1)
            self.check_status()
            if self.status != 'running':
                ret = 1
                break
        if not ret:
            self.status = 'hang'
            self.log('<+> hang checked')

    def one_file_end(self, flag=0):
        if self.status != 'finish':
            return 0
        elif flag == 1:
            self.check_finish(1)
            self.log('<+> close the programs')
            self.wait_close()
        return 1

    # def check_main(self):
    #     for fname in FILE_LIST:
    #         self.open_file(fname)
    #         print(fname)
    #         self.check_one_file(curtime)
    #         if self.status != 'finish':
    #             self.log(self.status)
    #             break
    #     if self.status == 'finish':
    #         self.log('close main window')
    #         self.check_finish(1)

    def wait_close(self):
        if self.status == 'finish':
            for _ in range(30):
                time.sleep(1)
                if not self.app.is_process_running():
                    self.log('<+> program exit normally')
                    break

    # def start_up(self):
    #     try:
    #         self.run_windbg()
    #         # if self.check_start():
    #         self.check_main()
    #         if self.status == 'finish':
    #             self.wait_close()
    #     except Exception as e:
    #         self.status = 'error'
    #         print(e)

    #     self.clean_status()
    #     return self.status


# if __name__ == "__main__":
#     m = Monitor(sys.argv[1])
#     m.start_up()
