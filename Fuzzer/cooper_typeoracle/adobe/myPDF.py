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

from PdfPaser.pdf import PdfFileParser
from PdfPaser.generic import DictionaryObject, ArrayObject, NameObject, IndirectObject, DecodedStreamObject
import os
import random
import copy

config_path = 'config'

def pdf_append_object(pdf, obj):
    pdf._objects.append(obj)
    return IndirectObject(len(pdf._objects), 0, None)

def get_page_ids(pdf):
    root_id = pdf._root.idnum
    catalog = pdf._objects[root_id-1]
    obj_queue = [catalog['/Pages'].idnum]
    page_list = []
    pages_list = []
    i = 0
    while i < len(obj_queue):
        objid = obj_queue[i]
        obj = pdf._objects[objid-1]
        if '/Type' in obj and obj['/Type'] == '/Pages' or '/Kids' in obj:
            if objid not in pages_list:
                pages_list.append(objid)
                if '/Kids' in obj:
                    kids_arr = obj['/Kids']
                    while isinstance(kids_arr, IndirectObject):
                        kids_arr = pdf._objects[kids_arr.idnum-1]
                    if isinstance(kids_arr, ArrayObject):
                        for o in kids_arr:
                            if isinstance(o, IndirectObject) and o.idnum not in obj_queue:
                                obj_queue.append(o.idnum)
        else:
            if '/Type' in obj and obj['/Type'] == '/Page' and objid not in page_list:
                page_list.append(objid)
        i += 1
    return pages_list, page_list


def pdf_add_js(pdf, jscode):
    try:
        _, pageids = get_page_ids(pdf)
        firstpidx = pageids[0] - 1
        print("firstpidx:%d"%(firstpidx))
        pageobj = pdf._objects[firstpidx]
        while isinstance(pageobj, IndirectObject):
            pageobj = pdf._objects[pageobj.idnum - 1]
        pageobj = pdf._objects[firstpidx]
        open_action = DictionaryObject()
        js_action = DictionaryObject()
        js_object = DecodedStreamObject()
        pageobj[NameObject('/AA')] = open_action
        open_action[NameObject('/O')] = js_action
        js_action[NameObject('/Type')] = NameObject('/Action')
        js_action[NameObject('/S')] = NameObject('/JavaScript')
        js_action[NameObject('/JS')] = pdf_append_object(pdf, js_object)
        js_object.setData(jscode)
    except Exception as e:
        print(e)
        return False
    else:
        return True


def pdf_get_js(pdf):
    res = None
    target_key = NameObject('/JS')
    target_key2 = NameObject('/AA')
    for pdf_obj in pdf._objects:
        # print(type(pdf_obj))
        if isinstance(pdf_obj, ArrayObject) or isinstance(pdf_obj, NameObject):
            continue
        if target_key in pdf_obj.keys():
            js_object = pdf_obj[target_key]
            if isinstance(js_object, IndirectObject):
                js_object = pdf._objects[js_object.idnum - 1]
                return js_object
            return js_object
        if target_key2 in pdf_obj.keys():
            aa_obj = pdf_obj[target_key2]
            index0_obj = aa_obj[NameObject('/O')]
            if target_key in index0_obj.keys():
                js_object = index0_obj[target_key]
                if isinstance(js_object, IndirectObject):
                    js_object = pdf._objects[js_object.idnum - 1]
                    return js_object
                return js_object
    return res


pdf_cache = {}
def pdf_load(pdfpath):
    if pdfpath not in pdf_cache:
        pdf = PdfFileParser(pdfpath)
        if len(pdf_cache) > 20:
            del_key = random.choice(pdf_cache.keys())
            del pdf_cache[del_key]
        pdf_cache[pdfpath] = pdf
    return copy.deepcopy(pdf_cache[pdfpath])


def make_pdf(jscode, output_file):
    sample_path = os.path.join(config_path, 'pdf_sample.pdf')
    sample_pdf = pdf_load(sample_path)
    js_object = pdf_get_js(sample_pdf)
    if js_object == None:
        pdf_add_js(sample_pdf, jscode)
    else:
        js_object.setData(jscode)
    with open(output_file, "wb") as f:
        sample_pdf.write(f)

def main():
    sample_path = os.path.join(config_path, 'normal.pdf')
    sample_pdf = pdf_load(sample_path)
    print(sample_pdf._objects)
    js_object = pdf_get_js(sample_pdf)
    if js_object == None:
        return
    print(js_object.getData())
    js_object.setData("console.show()")
    # pdf_add_js(sample_pdf, "console.show()")
    print(sample_pdf._objects)
    with open("pdf_js_sample.pdf", "wb") as f:
        sample_pdf.write(f)



if __name__ == '__main__':
    main()