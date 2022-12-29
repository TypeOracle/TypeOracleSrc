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

INPUT_DIR = 'output_dir'
OUTPUT_FNAME = 'ins_count.txt'

def parse(fpath):
	with open(fpath,'r') as f:
		raw = f.read()
	rlst = [i for i in raw.split('\n') if len(i)>0]
	nlst = []
	for i in rlst:
		a,b = i.split(',')
		nlst.append(int(b))

	return nlst

def combine(lst1,lst2):
	r = []
	for i,j in zip(lst1,lst2):
		r.append(i+j)
	return r

flst = os.listdir(INPUT_DIR)
plst = [os.path.join(INPUT_DIR,i) for i in flst]
datalst = [parse(i) for i in plst]

init = datalst[0][:]

for i in datalst[1:]:
	init = combine(init,i)

r = ['%d,%d'%(ind,i) for ind,i in enumerate(init)]

with open(OUTPUT_FNAME,'w') as f:
	f.write('\n'.join(r))