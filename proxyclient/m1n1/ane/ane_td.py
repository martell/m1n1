# SPDX-License-Identifier: MIT

import struct
from m1n1.utils import Register32

class HDR0(Register32):
    TID = 31, 24
    NID = 23, 16
    LNID = 15, 8
    EON = 7, 0

def pack_reg32(reg):
    return struct.pack('<L', reg._value)

def unpack_reg32(buf):
    return struct.unpack('<L', buf)[0]

def set_nid_in_buf(td_buf, nid):
    assert((nid > 0) and (nid < 0xff))
    hdr0 = HDR0(unpack_reg32(td_buf[:4]))
    hdr0.NID = nid
    repacked = pack_reg32(hdr0) + td_buf[4:]
    return repacked


class Task:
    def __init__(self, setupdict):
        self.req_iova = None
        self.nid = None
        self.bar = None
        self.size = None
        self.count = None
        for key in setupdict:
            setattr(self, key, setupdict[key])
        return

    def setup_BAR(self, bardict):
        self.bar = BAR()
        for key in bardict:
            setattr(self.bar, key, bardict[key])
        return

class BAR:
    def __init__(self):
        self.p_head = 0
        self.p_krn = 0
        self.p_2 = 0
        self.p_intm = 0
        self.p_dst = 0
        self.p_src1 = 0
        self.p_src2 = 0
        self.p_7 = 0
        self.p_8 = 0
        self.p_9 = 0
        self.p_a = 0
        self.p_b = 0
        self.p_c = 0
        self.p_d = 0
        self.p_e = 0
        self.p_f = 0
        self.p_10 = 0
        self.p_11 = 0
        self.p_12 = 0
        self.p_13 = 0
        self.p_14 = 0
        self.p_15 = 0
        self.p_16 = 0
        self.p_17 = 0
        self.p_18 = 0
        self.p_19 = 0
        self.p_1a = 0
        self.p_1b = 0
        self.p_1c = 0
        self.p_1d = 0
        self.p_1e = 0
        self.p_1f = 0
        return

    def get_table(self):
        return list(vars(self).values())
