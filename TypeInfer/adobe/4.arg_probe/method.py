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

import pattern
import parse
import runtime
import json
import os

def log_tmp_data(argpattern):
	apiname = argpattern['api']
	fname = 'tmp'+'_'.join(apiname.split('.'))+'.json'
	with open(fname,'w') as f:
		f.write(json.dumps(argpattern))

def log_tofile(msg):
    with open('log.txt', 'a') as f:
        f.write(msg)


def log_error(argpattern, curid):
    apiname = argpattern['api']
    msg = '[runtime_error] %s: %s\n' % (apiname, curid)
    log_tofile(msg)


def log_arr_error(argpattern):
    apiname = argpattern['api']
    msg = '[runtime_error] %s - array\n' % apiname
    log_tofile(msg)


def probe_object(mt, arg_pattern, node_id):
    # 嗅探generic object(简称gobject)内部元素的类型
    # 对于其中的复杂类型 只判断其为array或是gobject
    # 复杂类型内部的元素类型 在判断完当前参数以后 再递归进行判断
    # 这个函数是没有状态的 且一次只判断一个参数/元素

    def set_req(cur_node, cur_id, new_keys):
        # 将当前参数设置为必填参数
        cur_node['req_type'][-1] = cur_id
        # 将'4'调整为对应的类型
        cur_key = cur_node['req_key'][-1]
        cur_node['key_rel'][cur_key] = new_keys
        # 在key_rel记录key之间的依赖关系 即当前key产生了哪些新key

        if len(cur_node['unpro_key']) > 0:
            # 通常情况下new_key出现时应该没有其它unpro_key的
            # 所以记录下特殊的情况
            msg = '[?] required keys appear before optional keys:\n\tAPI: %s , Cur_Key: %s , Unpro_key: %s , New_key: %s\n' % \
                (arg_pattern['api'], cur_key, ':'.join(
                    cur_node['unpro_key']), ':'.join(new_keys))
            log_tofile(msg)

        cur_node['unpro_key'].extend(new_keys)
        # 将这些新key记录到unpro_key中

    def set_opt(cur_node, cur_id):
        # 将当前参数设置为可选参数
        cur_key = cur_node['req_key'][-1]
        cur_node['req_key'] = cur_node['req_key'][:-1]
        cur_node['req_type'] = cur_node['req_type'][:-1]
        cur_node['opt_key'].append(cur_key)
        cur_node['opt_type'].append(cur_id)
        # 将key从req_key移动到opt_key中
        # 因为之前待判断的key默认在req_key中

    def set_empty(cur_node):
        # 移除当前的参数
        cur_node['req_key'] = cur_node['req_key'][:-1]
        cur_node['req_type'] = cur_node['req_type'][:-1]
        # 从req_key中移除当前key

    cur_node = arg_pattern['info'][node_id]

    if len(cur_node['pro_key']) == 0:
        # 大部分情况下是不会运行这一步的
        if len(cur_node['key_trace']) == 0:
            # 如果当前没有已处理的key 且key_trace的内容为空
            # 由于gobject类型的判别依据只是可能正确的key的列表
            # 所以需要与提供其它参数的情形进行对比 差分得到新出现的key
            # 这里即是想得到arg={}时keytrace的内容 以便与arg={k:v}时keytrace进行对比
            # 但待处理的key(Unpro_key)是已经由上层确定的
            print('[*] use empty gobject to get initial keytrace')
            ret = runtime.run_testcase(mt, arg_pattern, prefer=[node_id])
            if ret:
                # 运行出错时返回1
                del cur_node['pro_key']
                # 至少把pro_key删除掉 使得程序认为该node处理完毕 不会再管它
                log_error(arg_pattern, node_id)
                # 记录下该API运行时出现错误
                return None
            # 这里运行效率存在优化的空间
            # 最好可以只运行1到2次 运行9次有点耗时
            # 主要受制于pykd脚本 以9次为一轮
            key_lst, _ = parse.run_check()
            cur_node['key_trace'] = key_lst[-1]
            # 将最后一次的结果作为keytrace

    cur_key = cur_node['unpro_key'][0]
    cur_node['pro_key'].append(cur_key)
    cur_node['unpro_key'] = cur_node['unpro_key'][1:]
    # 更新状态 当前key从unpro_key转移到pro_key中
    # 即未处理的key列表与已处理的key列表

    cur_node['req_key'].append(cur_key)
    cur_node['req_type'].append('4')
    # 将当前key作为必填参数 因为这里的生成器默认只生成必填参数
    # 4代表待判断的参数

    print('[*] in-processing key: %s' % cur_key)
    ret = runtime.run_testcase(mt, arg_pattern, prefer=[node_id])
    if ret:
        set_empty(cur_node)
        log_tmp_data(arg_pattern)
        del cur_node['pro_key']
        log_error(arg_pattern, node_id)
        return None

    key_lst, res_lst = parse.run_check()

    if len(res_lst) > 0:
        # 得到明确的类型要求 (原始类型/Array)
        if len(res_lst) == 4:
            print('[+] special cases in adobe, all type are satisfied')
            res_lst = res_lst[:3]
            # 如果四种类型都满足 即adobe中的特殊情况
            # 没必要判断array内部的元素要求 删除之

        id_lst = []

        if 1 in res_lst:
            print('[+] Boolean match')
            id_lst.append('0')
        if 2 in res_lst:
            print('[+] Number match')
            id_lst.append('1')
        if 3 in res_lst:
            print('[+] String match')
            id_lst.append('3')
        if 4 in res_lst:
            print('[+] Array match')
            new_id = pattern.create_array(arg_pattern)
            # 如果是数组则要创建新的条目
            print('[+] create new array node: ' + new_id)
            id_lst.append(new_id)

        if len(id_lst) > 1:
            cur_id = pattern.create_value(arg_pattern, id_lst)
            print(
                '[+] multiple types match, create new (get exist) value node: '+cur_id)
            # 存在多个正确的类型 则创建一个value类型
        else:
            cur_id = id_lst[0]

        rand_res = res_lst[0]-1
        # res_lst返回的结果时1~4 对应的索引即0~3
        cur_trace = key_lst[rand_res]
        # 这个有点偷懒 如果有多种类型 直接选择第一个正确匹配的结果作为keylst
        # 因此以下会进行异常情况检测

        tmp = [key_lst[i-1] for i in res_lst]
        if not parse.check_equal(tmp):
            # 检查所有满足条件的类型 得到的keytrace是否相等
            msg = "[?] different correct types lead to different keytraces\n\tAPI: %s , Key: %s\n" % (
                arg_pattern['api'], cur_key)
            arr = ['boolean', 'number', 'string', 'array']
            for i in res_lst:
                output = '\ttype: %s , keytrace: %s\n' % (
                    arr[i-1], repr(key_lst[i-1]))
                msg += output
            log_tofile(msg)
        # 检查代码结束 其实只是记录一下特殊情况
        # 本身value类型就少 大概率是完全不影响的

        new_keys = parse.compare_key(cur_node['key_trace'], cur_trace, cur_key)
        # 比较提供当前类型的参数与不提供当前参数 keytrace的变化
        # 为了判定参数是可选还是必填的

        if len(new_keys) > 0:
            print('[+] find new keys: '+','.join(new_keys))
            print('[=] considered as required key: ' + cur_key)
            set_req(cur_node, cur_id, new_keys)
            # 设置当前key的类型
            cur_node['key_trace'] = cur_trace
            # 在必填的情况下都需要更新key_trace 后续以该keytrace为基准进行比较
        else:
            print('[=] considered as optional key: ' + cur_key)
            set_opt(cur_node, cur_id)
            # 设置为可选的key

    else:
        # 没有检测出明确的类型的情况 可能时参数为空或是泛object类型(非array)
        # 主要利用keytrace进行判断
        print('[=] NO TYPE match, may be empty or object')

        if parse.check_equal(key_lst):
            # 所有类型得到的keytrace都完全相同
            print('[*] all the keytraces are the same')
            new_keys = parse.compare_key(
                cur_node['key_trace'], key_lst[0], cur_key)
            # 因为内容都相同 取首个元素进行比较
            if len(new_keys) > 0:
                # 如果出现了新的key 则认为时必填的value类型
                print('[+] find new key: '+','.join(new_keys))
                print('[+] regarded as required value: ' + cur_key)
                set_req(cur_node, '5', new_keys)
                # value即是任何类型都符合要求
                # 大概率是未知类型 或是路径条件不满足导致参数没有被进一步的处理
                cur_node['key_trace'] = key_lst[0]
            else:
                # 否则则认为是空参数 这个把这个key给去除
                # 可选的value类型实在没法判断
                print('[-] regarded as empty: '+cur_key)
                set_empty(cur_node)
        else:
            new_keys = parse.compare_key(
                cur_node['key_trace'], key_lst[-1], cur_key)
            # 检查提供array/gobject时 是否出现新的key
            # 但实际上只比较了gobject的keytrace

            if not parse.check_equal(key_lst[3:]):
                # 记录提供array和object时 keytrace不同的特殊情况
                msg = "[?] keytrace in array and gobject are different\n\tAPI: %s , Key: %s\n\tarray: %s\n\tobject: %s\n" % (
                    arg_pattern['api'], cur_key, repr(key_lst[-2]), repr(key_lst[-1]))
                log_tofile(msg)

            if len(new_keys) > 0:
                # 出现新的key 则大概率必填object 小概率是gobject参数内部元素的key需求
                # 所以先当作必填object进行处理
                # 暂时不考虑必填object 其object为gobject的情况
                # 感觉也没那么难实现 不过确实没见过 暂时不管了
                print('[+] find new key: '+','.join(new_keys))
                if len(set(new_keys) & set(cur_node['pro_key'])) > 0:
                    # 特殊处理 app.alert oCheckbox为gobject类型参数
                    # 新key:cMsg与之前处理过的key重复 所以可以之前判断其为gobject参数
                    print('[*] new key should not appeared in processed keys')
                    print('[+] regarded new key as elements in optional object')
                    cur_id = pattern.create_object(arg_pattern, new_keys)
                    print('[+] create new object id : '+cur_id)
                    # 创建一个新的node 用于存放object
                    # 将new_keys都作为unhandle key
                    set_opt(cur_node, cur_id)
                    # 当前参数设置为可选object
                else:
                    print('[-] regarded as required object: '+cur_key)
                    set_req(cur_node, '2', new_keys)
                    # 其余情况下先将其当作必填的的key
                    cur_node['key_trace'] = key_lst[-1]
                    # key_trace之间用{}得到的结果 因为后续处理'2'类型时用的也是{}填坑
            elif parse.check_dec(cur_node['unpro_key'], key_lst[:3]):
                # 如果提供基本类型时 发现原本部分unpro_key没有出现
                # 三个原始类型中都要出现了unpro_key消失的现象
                # 则认为是可选object参数 提供原始类型使得参数处理过程提前中止
                # 导致部分unprokey没有出现
                print(
                    '[*] unprocessed keys disappear when processing basic types')
                print('[+] regarded as optional object : '+cur_key)
                set_opt(cur_node, '2')
            elif parse.check_error(key_lst):
                # 比较提供array/gobject与原始类型的keytrace明显的不一致
                # 则认为是可选object参数
                # 现在想想这一情况其实是可以覆盖check_dec这个判断条件的
                print('[*] keytrace of basic types are different with complex types')
                print('[+] regarded as optional object : '+cur_key)
                set_opt(cur_node, '2')
            else:
                # 其余未能考虑到的情况 只能先记录下来
                msg = "[?] unknown conditions\n\tAPI: %s , Key: %s , Node: %s\n" % (
                    arg_pattern['api'], cur_key, node_id)
                for i, j in zip(key_lst, ['boolean', 'number', 'string', 'array', 'object']):
                    tmp = '\tType: %s , KeyTrace: %s\n' % (j, repr(i))
                    msg += tmp
                log_tofile(msg)
                print('[?] unknown conditions, regared as empty')
                set_empty(cur_node)
                # 当作参数不存在

    if len(cur_node['unpro_key']) > 0:
        # 如果un_process_key 依然存在 则继续嗅探
        print('[*] remain unprocessed keys : '+','.join(cur_node['unpro_key']))
        print('[*] contine recursion')
        probe_object(mt, arg_pattern, node_id)
    # 否则对最终结果进行调整 将部分key对应的value设置为object参数
    else:
        # 首先检查relations中 是否有req_key对应的new_key完全没有出现在req_key/opt_key中
        # 且这个req_key为'2'类型时 则将参数修改为object newkeys作为object中的unpro_key

        correct_key = set(cur_node['req_key']) | set(cur_node['opt_key'])
        # correct_key为所有出现的key

        for key in cur_node['key_rel']:
            ind = cur_node['req_key'].index(key)
            cur_type = cur_node['req_type'][ind]

            # if cur_type != '2':
            #     continue

            key_lst = set(cur_node['key_rel'][key])
            if len(key_lst & correct_key) == 0:
                print(
                    '[*] potential required key : %s does not generate new key requirement' % key)
                print('[+] set it as optional key')

                cur_node['req_key'] = cur_node['req_key'][:ind] + \
                    cur_node['req_key'][ind+1:]
                cur_node['req_type'] = cur_node['req_type'][:ind] + \
                    cur_node['req_type'][ind+1:]
                # 将该key中req_key中移除

                if cur_type != '2':
                    cur_node['opt_key'].append(key)
                    cur_node['opt_type'].append(cur_type)
                # 如果是普通类型则直接加入Opt_key中
                elif key not in cur_node['opt_key']:
                    cur_id = pattern.create_object(
                        arg_pattern, cur_node['key_rel'][key])
                    print('[+] create new object id : '+cur_id)
                    cur_node['opt_key'].append(key)
                    cur_node['opt_type'].append(cur_id)
                    # 将其作为可选的key

        # add 06.13

        # 如果opt_key中只有一个元素则将其加入req_key中 例如addField
        # 因为opt_key被错误识别成req_key其实没什么影响
        # 但req_key别识别成opt_key时则会影响参数的连续性
        if len(cur_node['opt_key']) == 1:
            k, v = cur_node['opt_key'][0], cur_node['opt_type'][0]
            print('[+] only one opt key, set it as req : "%s"' % k)
            cur_node['req_key'].append(k)
            cur_node['req_type'].append(v)
            cur_node['opt_key'] = []
            cur_node['opt_type'] = []

        # end

        # 此时object节点已经处理完毕 还需进行reprobe
        # 因为某些object/value的类型需求只有在必填参数全部提供时才会出现
        # 而顺序嗅探时不满足这一条件 所以在所有key都确定以后要重新识别这些模糊的参数

        tmp = cur_node['req_type']  # +cur_node['opt_type']
        tmpkey = cur_node['req_key']  # +cur_node['opt_key']
        # 只关注req_key
        # 除非是出现opt_key在req_key之前的特殊情况

        if len(tmp) > 1 and ('2' in tmp or '5' in tmp):
            # 稍微优化一下 如果只有一个object类型的参数则没必要reprobe了
            # 如果存在类型不明确的参数
            print('[+] unclear type detect, begin to reprobe current node')

            for ind, i in enumerate(tmp):
                if i == '2' or i == '5':
                    cur_key = tmpkey[ind]
                    cur_val = i
                    print('[*] reprobe key "%s" , value "%s"' %
                          (cur_key, cur_val))

                    cur_node['req_type'][ind] = '4'

                    ret = runtime.run_testcase(
                        mt, arg_pattern, prefer=[node_id])
                    # ret = runtime.run_testcase2(mt, arg_pattern)
                    # run_testcase2会强制提供全部的可选参数
                    # 感觉追加了最后一个可选参数为必填的设定后 就没有必要了
                    if ret:
                        cur_node['req_type'][ind] = cur_val
                        # 恢复原有状态
                        log_error(arg_pattern, node_id)
                        return
                    _, res_lst = parse.run_check()
                    # 之前提到过不考虑必填gobject 因为确实没见过
                    # 这里也不会处理keytrace

                    if len(res_lst) == 0:
                        cur_node['req_type'][ind] = cur_val
                        # 如果还是没有识别出类型则回归原样
                    else:
                        # 以下代码应当包装成函数
                        if len(res_lst) == 4:
                            res_lst = res_lst[:3]

                        id_lst = []
                        if 1 in res_lst:
                            print('[+] Boolean match')
                            id_lst.append('0')
                        if 2 in res_lst:
                            print('[+] Number match')
                            id_lst.append('1')
                        if 3 in res_lst:
                            print('[+] String match')
                            id_lst.append('3')
                        if 4 in res_lst:
                            print('[+] Array match')
                            new_id = pattern.create_array(arg_pattern)
                            print('[+] create new array node: ' + node_id)
                            id_lst.append(new_id)

                        if len(id_lst) > 1:
                            cur_id = pattern.create_value(arg_pattern, id_lst)
                            print(
                                '[+] multiple results, create new value node: '+cur_id)
                        else:
                            cur_id = id_lst[0]

                        cur_node['req_type'][ind] = cur_id

                        # cur_node['req_type'] += cur_node['opt_type']
                        # cur_node['req_key'] += cur_node['opt_key']
                        # cur_node['opt_type'] = []
                        # cur_node['opt_key'] = []
                        # 这里要考虑一下是否要这么做 把所有可选的key都作为必填的key

        del cur_node['key_trace']
        del cur_node['key_rel']
        del cur_node['pro_key']
        del cur_node['unpro_key']
        # 删除中间信息

        pattern.check_same_object(arg_pattern, node_id)
        # 如果存在与自己一模一样的节点 则删除自身 并修改之前的描述


def probe_array(mt, arg_pattern, node_id):
    # 处理array中的元素信息
    cur_node = arg_pattern['info'][node_id]

    if len(cur_node['req_type']) == 0:
        # 由函数return前设置下一轮的pattern
        # 但首个参数还是得在这里设置
        cur_node['req_type'].append('4')
        cur_node['is_pro'] = 1
        # 标记参数已经被处理 or 在处理中

    ret = runtime.run_testcase(mt, arg_pattern, prefer=[node_id])
    if ret:
        print('[!] runtime error, current array info: ' +
              ','.join(cur_node['req_type']))
        del cur_node['is_pro']
        cur_node['req_type'] = []
        # 把4移除 否则会影响之后的嗅探
        log_arr_error(arg_pattern)
        return None

    tmp_klst, res_lst = parse.run_check()
    end_flag = 0
    # 用于标识参数判断是否结束

    json_keys = []

    if len(res_lst) == 0:
        f, ks = parse.check_json_in_array(tmp_klst)
        if f == 1:
            # unidentified object
            res_lst.append(5)
        elif f == 2:
            # gobject
            # 这样获取的key未必准确
            # 但不管了 本来我还不想处理gobject的
            res_lst.append(6)
            json_keys = ks[:]

    if len(res_lst) == 0:
        # 没有识别出参数类型
        if len(cur_node['req_type']) == 1:
            print(
                '[*] failed to identified the first element, try to adjust the number of parameters %d' % len(cur_node['req_type']))
            # 首个参数没能正常识别 则增加其参数个数 尝试满足其数量要求
            cur_node['req_type'].append('5')
        else:
            if cur_node['req_type'][0] == '4':
                # 首个参数未能正常识别 此时正处于试探参数数量要求的阶段
                if len(cur_node['req_type']) < 4:
                    print(
                        '[*] maybe the number of parameters are not satified, increase the number %d' % len(cur_node['req_type']))
                    cur_node['req_type'].append('5')
                else:
                    # 数量超长
                    print(
                        '[+] exceed the maxiumium length, regarded as emtpy')
                    end_flag = 1
                    cur_node['req_type'] = []
            else:
                # 依次嗅探 直到嗅探不如新添加参数的类型
                end_flag = 1
                print('[*] reach the end of the array')
                ind = cur_node['req_type'].index('4')
                # 按理说4应该时最后一个参数 不过保险起见还是直接从'4'开始移除
                cur_node['req_type'] = cur_node['req_type'][:ind]
    else:
        # 如果识别出了参数的类型

        if cur_node['req_type'][0] == '4' and len(cur_node['req_type']) > 1:
            # 此时处于试探参数个数的阶段
            cur_node['req_num'] = len(cur_node['req_type'])
            # 记录参数的最低个数
            print('[+] find the min requirement of parameter : %d' %
                  cur_node['req_num'])

        if 1 in res_lst and 2 in res_lst and 3 in res_lst:
            # 由于新加入了一些res_lst 所以保险起见采用新的判断方式
            print('[+] sp cases in adobe ,all type are fine, exclude array')
            res_lst = [1, 2, 3]

        id_lst = []
        if 1 in res_lst:
            print('[+] Boolean match')
            id_lst.append('0')
        if 2 in res_lst:
            print('[+] Number match')
            id_lst.append('1')
        if 3 in res_lst:
            print('[+] String match')
            id_lst.append('3')
        if 4 in res_lst:
            print('[+] Array match')
            new_id = pattern.create_array(arg_pattern)
            print('[+] create new array node: ' + new_id)
            id_lst.append(new_id)

        if 5 in res_lst:
            print('[+] other object type match')
            id_lst.append('2')

        if 6 in res_lst and (arg_pattern['root'] != node_id or cur_node['req_type'][0] != '4'):
            # 如果当前嗅探rootnode 且嗅探首个参数则不处理json
            # 否则就和probe asobject重叠了
            print('[+] maybe generic object')
            print('[+] new keys: '+','.join(json_keys))
            cur_id = pattern.create_object(arg_pattern, json_keys)
            print('[+] create new object id : '+cur_id)
            id_lst.append(cur_id)

        if len(id_lst) > 1:
            cur_id = pattern.create_value(arg_pattern, id_lst)
            print('[+] create new value node: '+cur_id)
        else:
            cur_id = id_lst[0]

        ind = cur_node['req_type'].index('4')
        cur_node['req_type'][ind] = cur_id
        # 将4转化为正确的类型

        firstid = set([i[0] for i in cur_node['req_type']])

        if (node_id == arg_pattern['root'] and len(cur_node['req_type']) >= 7 and len(firstid) == 1) \
                or (len(cur_node['req_type']) >= 4 and len(firstid) == 1) \
                or len(cur_node['req_type']) >= 10:
            # 判断循环 / 避免死循环
            # 规则1 当前是root节点 (app.popUpMenu) array长度大于等于7 且始终是同一类型 (确实见过连续4个string类型参数在root节点中出现过)
            # 规则2 当前非root节点 (resetForm) array长度大于等于4 且始终是同一类型
            # 规则3 参数长度大于等于10
            # 类型一致的条件 只要是首个typeid字母一样就行 不要求完全一致
            print(
                '[+] find circulation ,or exceed the max number')
            end_flag = 1
        else:
            if ind+1 == len(cur_node['req_type']):
                # 根据'4'所在的位置 设置待识别参数的位置
                cur_node['req_type'].append('4')
            else:
                cur_node['req_type'][ind+1] = '4'
            print('[*] update arglst in array : ' +
                  ','.join(cur_node['req_type']))

    if end_flag:
        # 根据req_num划分req_type和opt_type
        print('[+] array extracted end, begin to divide the required args')
        cur_node['opt_type'] = cur_node['req_type'][cur_node['req_num']:]
        cur_node['req_type'] = cur_node['req_type'][:cur_node['req_num']]

        if len(cur_node['req_type']) < cur_node['req_num']:
            # 特殊情况 存在最低数量要求 但在数量要求内有元素没能成功识别
            # 因为之前从'4'开始移除req_type的内容
            # 所以现在填充回来 ps: 好像当时直接把'4'改成'5'就行了
            while True:
                cur_node['req_type'].append('5')
                if len(cur_node['req_type']) == cur_node['req_num']:
                    break

        del cur_node['req_num']
        del cur_node['is_pro']

        # app.popUpMenu 特殊情况
        # 有时例如发现元素全是数组时采用同样的策略
        # 可能在popUpMenuEx中也能使用
        tmp = cur_node['opt_type']
        stmp = []
        for i in tmp:
            if i.startswith('5'):
                stmp.append('5')
            elif i.startswith('22'):
                stmp.append('22')
            elif i.startswith('23'):
                stmp.append('23')
        stmp = set(stmp)
        ltmp = [i for i in tmp if len(i) > 1]
        # 全是复杂类型 / 原类型长度超过4 / 只有一种复杂类型
        if len(ltmp) == len(tmp) and len(tmp) >= 4 and len(stmp) == 1:
            print('[*] combine duplicate nodeid: '+','.join(tmp))
            for ids in cur_node['opt_type'][1:]:
                if ids in arg_pattern['info']:
                    if ids.startswith('5'):
                        tmp_node = arg_pattern['info'][ids]
                        r = [i for i in tmp_node['typelist'] if len(i) > 1]
                        for k in r:
                            # 将节点内部的复杂元素删除
                            print('[-] delete recursion node: '+k)
                            del arg_pattern['info'][k]
                    # 删除节点自身
                    del arg_pattern['info'][ids]
                    print('[-] delete node: '+ids)

            cur_node['opt_type'] = [cur_node['opt_type'][0]
                                    for i in range(len(tmp))]  # range(len(tmp))]
        # app.popUpMenu是循环 每个数组元素中可能会嵌套数组 就造成7+7*10次的迭代
        # 现在优化一下 在第一层node处理完成后 将类型全部设置为同一node 这样造成7+10次迭代

        pattern.check_same_array(arg_pattern, node_id)
        # 检查自身是否内容重复

    else:
        # 没有结束 继续递归
        print('[*] continue recursion')
        probe_array(mt, arg_pattern, node_id)

# 分开处理object和array
# 没那么在乎效率 实在不行让monitor能在函数间传递


def check_unprocessed_node(argpattern,level=2):
    def filter_complex(typelst):
        return [i for i in typelst if len(i) > 1]
        # 长度大于1的id为复杂类型

    def checklevel(dic, key):
        # 检查nodeid在整个参数信息中处于的层级
        path = [key]
        tmp = key
        while True:
            if tmp in dic:
                # dic记录nodeid的上一级
                # rootnode下的内容不记录在dic中
                tmp = dic[tmp]
                path.append(tmp)
            else:
                break
        path = [i for i in path if not i.startswith('5')]
        path.reverse()
        # 忽略value

        print('->'.join(path))

        # 也就是最多两级
        # 例如addField中 rootid->{oCoord:<value>}->[array of <number>]
        # 如果这个array中还包含复杂类型就不会继续嗅探下去
        if len(path) <= level:
            return True
        else:
            return False

    dep = {}
    for i in argpattern['info']:
        cur_node = argpattern['info'][i]
        if i.startswith('23') or i.startswith('22'):
            tmp = filter_complex(
                cur_node['req_type']+cur_node['opt_type'])
            for t in tmp:
                dep[t] = i
        elif i.startswith('5'):
            tmp = filter_complex(cur_node['typelist'])
            for t in tmp:
                dep[t] = i
        # 这里可能存在一点bug 例如同一个typeid出现在不同node中
        # 不过由于只有两层 应该也不会出问题
        # 因为第一层的节点只有一个(root指向) 嗅探第二层节点时id时独一无二的 而第三层节点则不会处理

    res = []
    for node_id in argpattern['info']:
        cur_node = argpattern['info'][node_id]
        if node_id.startswith('23'):
            if 'pro_key' in cur_node and len(cur_node['pro_key']) == 0:
                # 处理完成的节点pro_key是被删除的
                # 初始阶段pro_key存在但没有任何内容 后一个条件好像没有必要
                res.append(node_id)
        elif node_id.startswith('22'):
            if 'is_pro' in cur_node and cur_node['is_pro'] == 0:
                res.append(node_id)

    res = [i for i in res if checklevel(dep, i)]
    # 记录前两层 未处理的node
    print('[+] unclear node id: %s' % ','.join(res))

    return res


def handle_method_asobject(apiname):

    print('[*] probe the method "%s"(object)' % apiname)

    print('[*] init monitor framework')
    mt, err = runtime.init_runtime()

    if err == 1:
        print('[!] framework failed to init')
        mt.clean_status()
        return {}
        # 此时返回完全为空的{}
        # 可以在上层用过len(res.keys())==0来判断运行出错

    # 先用完全空的参数跑一遍
    # 再用(arg)跑一遍
    # 没那么在乎效率

    argpattern0 = {'api': apiname, 'apitype': 0, 'root': '220',
                   'info': {'220': {'req_type': [], 'opt_type': []}}}
    print('[+] run with empty args:%s()' % apiname)
    ret = runtime.run_testcase(mt, argpattern0)
    # 使用空参数运行一遍  this.testapi()
    if ret:
        return {}

    print('[+] get basis keytrace')
    key_lst, _ = parse.run_check()
    old_lst = key_lst[-1]
    # 获取最后一组产生的keytrace
    # 第一组载入模块可能会产生扰动

    argpattern = {'api': apiname, 'apitype': 0, 'root': '230',
                  'info': {'230': {
                      'req_key': [], 'req_type': [],
                      'opt_key': [], 'opt_type': [],
                      'key_trace': [], 'key_rel': {},
                      'pro_key': [], 'unpro_key': []}}}
    print('[+] run with empty object:%s({})' % apiname)
    ret = runtime.run_testcase(mt, argpattern)

    if ret:
        return {}

    print('[+] get initial keytrace')

    key_lst, _ = parse.run_check()
    cur_lst = key_lst[-1]
    # 没必要运行9遍的 万一有弹窗还是挺耗时的 以后再优化吧
    # 记录this.testapi({})产生的keytrace

    new_keys = parse.compare_key(old_lst, cur_lst)

    if len(new_keys) == 0:
        # 理论上没有新key 认为不能以object的方式传参
        new_keys = parse.compare_key([], cur_lst)
        # app.popUpMenuEx的特殊情况
        # 强行将({})得到的key作为结果
        if len(new_keys) == 0:
            # 此时再没有新key就真的认为不需要参数了
            print('[=] empty inital keylst,may be inadapte with object args')
            runtime.close_runtime(mt)
            return argpattern

    print('[+] intial keylst:'+','.join(new_keys))
    argpattern['info']['230']['unpro_key'] = new_keys
    argpattern['info']['230']['key_trace'] = cur_lst

    while True:
        reslst = check_unprocessed_node(argpattern)
        # 检查是否存在未嗅探出类型的节点 例如刚才新建的230
        if len(reslst) == 0:
            print('[=] all node information are clear')
            break
        cur_id = reslst[0]
        print('[*] probe the information of node: %s' % cur_id)
        # 取出首个元素
        if cur_id.startswith('23'):
            probe_object(mt, argpattern, cur_id)
        elif cur_id.startswith('22'):
            probe_array(mt, argpattern, cur_id)

    print('[*] close target programs')
    runtime.close_runtime(mt)

    return argpattern


def handle_method_asarray(apiname):

    print('[*] probe the method "%s"(array)' % apiname)

    argpattern = {'api': apiname, 'apitype': 0, 'root': '220',
                  'info': {'220': {'req_type': [], 'opt_type': [],
                                   'req_num': 0, 'is_pro': 0}}}
    mt, err = runtime.init_runtime()

    if err == 1:
        print('[!] framework failed to init')
        mt.clean_status()
        return {}

    argpattern0 = {'api': apiname, 'apitype': 0, 'root': '220',
                   'info': {'220': {'req_type': [], 'opt_type': []}}}
    print('[+] run with empty args:%s()' % apiname)
    ret = runtime.run_testcase(mt, argpattern0)
    # 使用空参数运行一遍  this.testapi() 载入模块
    if ret:
        return {}

    # 以下代码可以包装成函数
    while True:
        reslst = check_unprocessed_node(argpattern)
        if len(reslst) == 0:
            print('[=] all node information are clear')
            break
        cur_id = reslst[0]
        print('[*] probe the information of node: %s' % cur_id)
        if cur_id.startswith('23'):
            probe_object(mt, argpattern, cur_id)
        elif cur_id.startswith('22'):
            probe_array(mt, argpattern, cur_id)

    print('[*] close target programs')
    runtime.close_runtime(mt)

    return argpattern


def handle_setter(apiname):
    # 认为setter不会有generic object类型
    # 因此处理逻辑比较直观

    print('[*] probe the property "%s"(setter)' % apiname)

    argpattern = {'api': apiname, 'apitype': 1, 'root': '4',
                  'info': {}}
    mt, err = runtime.init_runtime()

    if err == 1:
        print('[!] framework failed to init')
        mt.clean_status()
        return {}

    argpattern0 = {'api': apiname, 'apitype': 0, 'root': '5',
                   'info': {}}
    print('[+] run with empty args:%s=1' % apiname)
    ret = runtime.run_testcase(mt, argpattern0)
    # 使用空参数运行一遍  this.setter=1 载入模块
    if ret:
        return {}

    ret = runtime.run_testcase(mt, argpattern)
    if ret:
        return {}

    _, res_lst = parse.run_check()

    if len(res_lst) == 0:
        print('[=] the property may not implement the setter handler')
        argpattern['root'] = 5
        # 5表明可能不是setter
        # 不过在adobe中通过dispatcher都是实现setter
        # 所以就用随机的value了
    else:
        if len(res_lst) == 4:
            res_lst = res_lst[:3]

        id_lst = []
        if 1 in res_lst:
            id_lst.append('0')
            print('[+] boolean match')
        if 2 in res_lst:
            id_lst.append('1')
            print('[+] number match')
        if 3 in res_lst:
            id_lst.append('3')
            print('[+] string match')
        if 4 in res_lst:
            new_id = pattern.create_array(argpattern)
            print('[+] array match')
            id_lst.append(new_id)

        if len(id_lst) > 1:
            cur_id = pattern.create_value(argpattern, id_lst)
        else:
            cur_id = id_lst[0]

        argpattern['root'] = cur_id

    while True:
        reslst = check_unprocessed_node(argpattern)
        if len(reslst) == 0:
            print('[=] all node information are clear')
            break
        cur_id = reslst[0]
        print('[*] probe the information of node: %s' % cur_id)
        # 其实23可以省略掉 无所谓了
        if cur_id.startswith('23'):
            probe_object(mt, argpattern, cur_id)
        elif cur_id.startswith('22'):
            probe_array(mt, argpattern, cur_id)

    print('[*] close target programs')
    runtime.close_runtime(mt)

    return argpattern


def shrink_pattern(argpattern):
    # 合并内容重复的node
    # 最多合并空的array 暂时不实现也没什么问题
    pass


def main():
    with open('funclst.txt', 'r') as f:
        raw = f.read()
    funclst = [i for i in raw.split('\n') if len(i) > 0]
    with open('setterlst.txt', 'r') as f:
        raw = f.read()
    setterlst = [i for i in raw.split('\n') if len(i) > 0]

    for apiname in funclst[:]:
        print('[+] current apiname : '+apiname)
        try:
            args = handle_method_asobject(apiname)
            if len(args.keys()) == 0:
                msg = '[!!!] error in apiname "%s"\n' % (apiname)
                log_tofile(msg)
            else:
                fname = '_'.join(apiname.split('.'))+'.json'
                fpath = os.path.join('method_object', fname)
                with open(fpath, 'w') as f:
                    f.write(json.dumps(args))
        except Exception as e:
            print(e)

        try:
            args = handle_method_asarray(apiname)
            if len(args.keys()) == 0:
                msg = '[!!!] error in apiname "%s"\n' % (apiname)
                log_tofile(msg)
            else:
                fname = '_'.join(apiname.split('.'))+'.json'
                fpath = os.path.join('method_array', fname)
                with open(fpath, 'w') as f:
                    f.write(json.dumps(args))
        except Exception as e:
            print(e)

    for apiname in setterlst[:]:
        print('[+] current apiname : '+apiname)
        try:
            args = handle_setter(apiname)
            if len(args.keys()) == 0:
                msg = '[!!!] error in apiname "%s"\n' % (apiname)
                log_tofile(msg)
            else:
                fname = '_'.join(apiname.split('.'))+'.json'
                fpath = os.path.join('setter', fname)
                with open(fpath, 'w') as f:
                    f.write(json.dumps(args))
        except Exception as e:
            print(e)

# TODO
# 新建handle_result.py
# 根据结果选择用gobject还是array作为root节点 easy


if __name__ == '__main__':
    for dirname in ['method_object','method_array','setter']:
        if not os.path.exists(dirname):
            os.makedirs(dirname)
    main()

    # #apiname = 'this.Collab.setReviewFolderForMultipleReviews'
    # apiname = 'this.addField'
    # #apiname = 'this.app.alert'
    # apiname = 'this.getUIPerms'
    # print('[+] current apiname : '+apiname)
    # #args = handle_method_asarray(apiname)
    # args = handle_method_asarray(apiname)
    # #args = handle_setter(apiname)
    # fname = '_'.join(apiname.split('.'))+'.json'
    # with open(fname, 'w') as f:
    #     f.write(json.dumps(args))
