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
import shutil
import subprocess

TMPDIR = 'tmp'
TESTDIR = 'test'

def generate_js(jsnum):
	if os.path.exists(TMPDIR):
		shutil.rmtree(TMPDIR)
	# os.makedirs(TMPDIR)
	cmd = 'node Generator\\Run\\Gen.js -r -o %s -n %d'%(TMPDIR,jsnum)
	print(cmd)
	p = subprocess.Popen(cmd,shell=True)
	p.wait()
	print('finish generating')
	js_num = len(os.listdir(TMPDIR))
	while js_num ==0:
		if os.path.exists(TMPDIR):
			shutil.rmtree(TMPDIR)
		# os.makedirs(TMPDIR)
		cmd = 'node Generator\\Run\\Gen.js -r -o %s -n %d'%(TMPDIR,jsnum)
		print(cmd)
		p = subprocess.Popen(cmd,shell=True)
		p.wait()
		print('finish generating again')
		js_num = len(os.listdir(TMPDIR))
	for ind,fname in enumerate(os.listdir(TMPDIR)):
		ori_fpath = os.path.join(TMPDIR,fname)
		new_fpath = os.path.join(TMPDIR,'%d.js'%ind)
		os.rename(ori_fpath,new_fpath)
		with open(new_fpath,'a') as f:
			f.write(';closeDoc(1);')
	print('finish rename')

def combine_pdf():
	if not os.path.exists(TESTDIR):
		os.makedirs(TESTDIR)
	base_ind = len(os.listdir(TESTDIR))
	corpus_len = len(os.listdir(TMPDIR))
	for i in range(corpus_len):
		cmd = 'ruby Generator\\Run\\addjs.rb Generator\\Run\\blank.pdf tmp\\%d.js test\\%d.pdf'%(i,i+base_ind)
		print(cmd)
		p = subprocess.Popen(cmd,shell=True)
		p.wait()

def main():
	generate_js(10)
	combine_pdf()

if __name__ == '__main__':
	main()