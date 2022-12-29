/*
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
*/

#include "pin.H"
#include <fstream>
#include <iostream>
#include <unordered_set>

using std::endl;
using std::hex;
using std::ofstream;
using std::string;
using std::tr1::unordered_set;

using std::cerr;
using std::cout;
using std::flush;

UINT32 count = 0;
UINT32 flag = 0;
// 0  |  1  |  ++ 2 ++  | 3 |  0
UINT32 sign = 0;
// 0  |  1  | 0

ADDRINT startaddr = 0xcae20;
ADDRINT endaddr = 0xcaf33;
ADDRINT methodcall = 0x52ab3;
ADDRINT methodend = 0x52ab5;
ADDRINT settercall = 0x3e197;
ADDRINT setterend = 0x3e199;

ofstream tracefile;

unordered_set<UINT32> imgidset;

// 2020.12.09 update
KNOB<string> KnobOutputFile(KNOB_MODE_WRITEONCE, "pintool",
                            "o", "trace.out", "specify file name for MyPinTool output");

VOID ModStart(void)
{
    flag = (flag + 1) % 4;

    if (flag == 2)
    {
        sign = 0;
        tracefile << "(+)" << endl;
    }
}

VOID ModEnd(void)
{
    flag = (flag + 1) % 4;

    if (flag == 3)
    {
        sign = 0;
        tracefile << "(-)" << endl;
    }
}

VOID RecStart(void)
{
    if (flag == 2)
    {
        count = 0;
        sign = 1;
        tracefile << "[+]" << endl;
    }
}

VOID RecEnd(void)
{
    if (flag == 2)
    {
        count = 0;
        sign = 0;
        if (count > 0x200000)
        {
            tracefile << "[-!]" << endl;
        }
        else
        {
            tracefile << "[-]" << endl;
        }
    }
}

VOID RecordMem(THREADID threadid, ADDRINT ip, VOID *addr, UINT32 refsize)
{
    if (sign != 1 || threadid != 0 || count > 0x200000)
        return;


    if (refsize == 4)
    {
        UINT32 val = *static_cast<UINT32 *>(addr);

        tracefile << ip << " " << val << endl;
        count++;
    }

}

VOID RecordReg(THREADID threadid, ADDRINT ip, ADDRINT regval)
{
    if (sign != 1 || threadid != 0 || count > 0x200000)
        return;

    UINT32 val = static_cast<UINT32>(regval);

    // if (val < 0x100000 || val > 0x80000000)
    // {
    //     return;
    // }

    tracefile << ip << " " << val << endl;
    count++;

}


VOID ImageLoad(IMG img, VOID *v)
{
    string fullname = IMG_Name(img);
    string iname = fullname.substr(fullname.rfind('\\') + 1);
    string fmt = iname.substr(iname.rfind('.') + 1);

    // if (!fmt.compare("api") || !iname.compare("AcroRd32.dll"))
    if (!fmt.compare("api"))
    {
        imgidset.insert(IMG_Id(img));
        tracefile << iname << ":" << IMG_LowAddress(img) << ":" << IMG_HighAddress(img) << endl;

        if (!iname.compare("EScript.api"))
        {
            startaddr += IMG_LowAddress(img);
            endaddr += IMG_LowAddress(img);
            methodcall += IMG_LowAddress(img);
            methodend += IMG_LowAddress(img);
            settercall += IMG_LowAddress(img);
            setterend += IMG_LowAddress(img);
        }
    }
}

VOID Trace(TRACE trace, VOID *v)
{
    INS head = BBL_InsHead(TRACE_BblHead(trace));
    RTN rtn = RTN_FindByAddress(INS_Address(head));

    if (!RTN_Valid(rtn))
        return;

    IMG img = IMG_FindByAddress(INS_Address(head));

    auto search = imgidset.find(IMG_Id(img));
    if (search == imgidset.end())
        return;

    for (BBL bbl = TRACE_BblHead(trace); BBL_Valid(bbl); bbl = BBL_Next(bbl))
    {
        INS ins_begin = BBL_InsHead(bbl);
        INS ins_end = BBL_InsTail(bbl);

        ADDRINT bbkstart = INS_Address(ins_begin);
        ADDRINT bbkend = INS_Address(ins_end);

        if (bbkstart == startaddr)
        {
            INS_InsertCall(ins_begin, IPOINT_BEFORE,
                           (AFUNPTR)ModEnd,
                           IARG_END);
        }
        else if (bbkstart == methodend || bbkstart == setterend)
        {
            INS_InsertCall(ins_begin, IPOINT_BEFORE,
                           (AFUNPTR)RecEnd,
                           IARG_END);
        }

        if (bbkend == endaddr)
        {
            INS_InsertCall(ins_end, IPOINT_BEFORE,
                           (AFUNPTR)ModStart,
                           IARG_END);
        }
        else if (bbkend == methodcall || bbkend == settercall)
        {
            INS_InsertCall(ins_end, IPOINT_BEFORE,
                           (AFUNPTR)RecStart,
                           IARG_END);
        }

        for (INS ins = BBL_InsHead(bbl); INS_Valid(ins); ins = INS_Next(ins))
        {
            OPCODE code = INS_Opcode(ins);

            if (code == XED_ICLASS_PUSH)
            {
                if (INS_OperandIsReg(ins, 0))
                {
                    REG reg = INS_OperandReg(ins, 0);
                    if (REG_Size(reg) == 4 && reg != REG_ESP && reg != REG_EBP)
                    {
                        INS_InsertPredicatedCall(
                            ins, IPOINT_BEFORE, (AFUNPTR)RecordReg,
                            IARG_THREAD_ID,
                            IARG_INST_PTR,
                            IARG_REG_VALUE, reg,
                            IARG_END);
                    }
                }
                else if (INS_OperandIsMemory(ins, 0))
                {
                    INS_InsertPredicatedCall(
                        ins, IPOINT_BEFORE, (AFUNPTR)RecordMem,
                        IARG_THREAD_ID,
                        IARG_INST_PTR,
                        IARG_MEMORYREAD_EA,
                        IARG_MEMORYREAD_SIZE,
                        IARG_END);
                }
            }
        }
    }
}

VOID Fini(INT32 code, VOID *v)
{
    tracefile.close();
}

int main(int argc, char *argv[])
{
    if (PIN_Init(argc, argv))
        return -1;

    string fileName = KnobOutputFile.Value();
    tracefile.open(fileName.c_str());
    tracefile << hex;

    IMG_AddInstrumentFunction(ImageLoad, 0);
    TRACE_AddInstrumentFunction(Trace, 0);
    PIN_AddFiniFunction(Fini, 0);

    PIN_StartProgram();

    return 0;
}
