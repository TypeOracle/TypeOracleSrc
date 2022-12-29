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

def parseastr(st):
	tmp = [int(st[i*2:i*2+2],16) for i in range(4)]
	tmp.reverse()
	nlst = []
	for i in tmp:
		if i!=0:
			nlst.append(chr(i))
		else:
			break
	return ''.join(nlst)

def parseustr(st):
	tmp = [int(st[i*4:i*4+4],16) for i in range(2)]
	tmp.reverse()
	nlst = []
	for i in tmp:
		if i!=0:
			nlst.append(chr(i))
		else:
			break
	return ''.join(nlst)

def generate(st):
	curst = st[:4]
	uni = []
	asc = []
	arr = [hex(ord(i))[2:] for i in curst]
	arr1 = arr[:2]
	if len(arr)<4:
		while True:
			arr.append('00')
			if len(arr)>=4:
				break
	arr.reverse()
	if len(arr1)==0:
		arr1 = ['00','00','00',arr1[0]]
	else:
		arr1 = ['00',arr1[1],'00',arr1[0]]
	return ''.join(arr),''.join(arr1)

def getallowedlst(fname,klst):
	with open(fname,'r') as f:
		d = json.loads(f.read())
	alst = []
	ulst = []
	for k in klst:
		a,u = generate(k)
		alst.append(a)
		ulst.append(u)
	res = {}
	for addr in d:
		lst = d[addr]
		flag = 1
		for i in alst:
			if i not in lst:
				flag = 0
				break
		if flag == 1:
			res[addr] = sorted([parseastr(i) for i in lst])
		flag = 1
		for i in ulst:
			if i not in lst:
				flag = 0
				break
		if flag == 1:
			res[addr] = sorted([parseustr(i) for i in lst])
	return res

def combinedic(diclst):
	tmp = [set(i.keys()) for i in diclst]
	initset = tmp[0]
	for i in tmp[1:]:
		initset = initset&i
	res = {}
	for i in initset:
		res[i] = {}
		for ind,dic in enumerate(diclst):
			res[i][ind] = dic[i]
	return res

if __name__ == '__main__':
	# for i in ['cName','nX','nY']:
	# 	a,b = generate(i)
	# 	print(a,b)


	flst = ['1.json','2.json','3.json']
	klst = [['cName'],['nX','nY'],['cName']]

	diclst = [getallowedlst(i,j) for i,j in zip(flst,klst)]
	r = combinedic(diclst)
	with open('result.json','w') as f:
		f.write(json.dumps(r))
	print(len(r.keys()))
	# with open('result.json','r') as f:
	# 	d = json.loads(f.read())

	# res = {}
	# for addr in d:
	# 	lst = d[addr]
	# 	if '0000586e' in lst and '0000596e' in lst:
	# 		res[addr] = sorted([parseastr(i) for i in lst])
	# 	elif '0058006e' in lst and '0059006e' in lst:
	# 		res[addr] = sorted([parseustr(i) for i in lst])

	# print(len(res.keys()))
	# with open('5.json','w') as f:
	# 	f.write(json.dumps(res))
