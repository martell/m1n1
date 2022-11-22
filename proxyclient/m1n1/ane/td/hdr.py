# SPDX-License-Identifier: MIT

import struct
from m1n1.utils import Register32

class HDR0(Register32):
    TID = 31, 24
    NID = 23, 16
    LNID = 15, 8 # nvr used
    UNK1 = 7, 0

def pack_reg32(reg):
    return struct.pack('<L', reg._value)

def unpack_reg32(buf):
    return struct.unpack('<L', buf)[0]

def get_nid_from_buf(td_buf):
    hdr0 = HDR0(unpack_reg32(td_buf[:4]))
    assert((hdr0.NID > 0) and (hdr0.NID < 0xff))
    return hdr0.NID & 0xff

def set_nid_in_buf(td_buf, nid):
    assert((nid > 0) and (nid < 0xff))
    hdr0 = HDR0(unpack_reg32(td_buf[:4]))
    hdr0.NID = nid
    repacked = pack_reg32(hdr0) + td_buf[4:]
    return repacked
