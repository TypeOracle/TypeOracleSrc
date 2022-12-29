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

import json

import runtime
import method

def handle_old_object(fname,nodeid):
	with open(fname,'r') as f:
		arg_pattern = json.loads(f.read())

	mt, err = runtime.init_runtime()

	if err == 1:
		print('[!] init failed')
		mt.clean_status()
		return 

	method.probe_object(mt, arg_pattern, nodeid)

	while True:
		reslst = method.check_unprocessed_node(arg_pattern,3)
		if len(reslst) == 0:
			print('[=] all node information are clear')
			break
		cur_id = reslst[0]
		print('[*] probe the information of node: %s' % cur_id)
		if cur_id.startswith('23'):
			method.probe_object(mt, arg_pattern, cur_id)
		elif cur_id.startswith('22'):
			method.probe_array(mt, arg_pattern, cur_id)
	print('[*] close target programs')
	runtime.close_runtime(mt)
	return arg_pattern

if __name__ == '__main__':
	fname = 'tmpthis_addAnnot.json'
	r = handle_old_object(fname,'230')
	with open(fname[3:],'w') as f:
		f.write(json.dumps(r))