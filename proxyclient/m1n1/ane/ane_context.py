# SPDX-License-Identifier: MIT

import os
import struct
from datetime import datetime
from dataclasses import dataclass

from m1n1.hw.ane import TD_HDR0
from m1n1.ane.ane_utils import roundup, nextpow2
from m1n1.ane.ane_utils import make_padding


@dataclass
class Buffer:
    mapid: int
    paddr: int
    vaddr: int
    size: int

class ANEBufManager:
    def __init__(self, ane):
        self.ane = ane
        self.mapid = 0
        self.map = {}
        self.dart_synced = False
        return

    def alloc_data(self, data):
        size = roundup(len(data), self.ane.PAGE_SIZE)
        paddr = self.ane.u.memalign(self.ane.PAGE_SIZE, size)
        self.ane.p.memset32(paddr, 0, size)
        vaddr = self.ane.dart.iomap(0, paddr, size)
        self.ane.iowrite(vaddr, data)
        
        buf = Buffer(self.mapid, paddr, vaddr, size)
        self.map[self.mapid] = buf
        print("mapid %d: mapped paddr 0x%x to vaddr 0x%x for data w/ size 0x%x"
              % (buf.mapid, buf.paddr, buf.vaddr, buf.size))
        self.mapid += 1
        return self.mapid

    def alloc_size(self, size):
        size = roundup(size, self.ane.PAGE_SIZE)
        paddr = self.ane.u.memalign(self.ane.PAGE_SIZE, size)
        self.ane.p.memset32(paddr, 0, size)
        vaddr = self.ane.dart.iomap(0, paddr, size)
        
        buf = Buffer(self.mapid, paddr, vaddr, size)
        self.map[self.mapid] = buf
        print("mapid %d: mapped paddr 0x%x to vaddr 0x%x for data w/ size 0x%x"
              % (buf.mapid, buf.paddr, buf.vaddr, buf.size))
        self.mapid += 1
        return self.mapid

    def flush_buf(self, buf):
        self.ane.iowrite(buf.vaddr, make_padding(buf.size))
        return

    def flush_mapid(self, mapid):
        flush_buf(self.map[mapid])
        return

    def run_syncttbr(self):
        if ((self.mapid > 0) and (self.dart_synced == False)):
            self.ane.syncttbr()
            self.dart_synced = True
        return

    def dump_map(self):
        for mapid in self.map:
            buf = self.map[mapid]
            print('mapid %d: paddr 0x%x, vaddr 0x%x, size 0x%x'
                  % (buf.mapid, buf.paddr, buf.vaddr, buf.size))
        return

    def dump_bufs(self):
        outdir = os.path.join('out', datetime.now().isoformat())
        os.makedirs(oudir, exist_ok=True)
        region = b''
        for mapid in self.map:
            buf = self.map[mapid]
            data = self.ane.ioread(buf.vaddr, buf.size)
            open(os.path.join(outdir, '0x%x.bin' % buf.vaddr), 'wb').write(data)
            region += data
        open(os.path.join(outdir, 'region.bin'), 'wb').write(region)
        return len(region)


class TaskSequence:
    # linear ll of task descriptors
    def __init__(self, ts_buf, ts_prop):
        # ts: only once; head of BAR in tq
        self.ts_buf = ts_buf
        self.ts_prop = ts_prop
        self.ts_bps = [roundup(prop, 0x100) for prop in self.ts_prop]
        self.td_count = len(self.ts_prop)

        # td: 0th td to populate fifo req pool
        self.td_buf = self.ts_buf[:self.ts_prop[0]]
        self.td_size = len(self.td_buf)
        return


class EngineReq:
    # hardware req struct
    def __init__(self, ts):
        self.ts = ts
        self.size = self.ts.td_size
        self.td_count = self.ts.td_count
        self.vaddr = None
        self.nid = None
        self.bar = None
        # self.prty = None # optional
        return

    def setup_BAR(self, mapid_dict):
        self.bar = BAR()
        for key in mapid_dict:
            setattr(self.bar, key, bardict[key])
        return


class ReqManager:

    REQ_FIFO_COUNT = 0x20

    def __init__(self, ane):
        self.ane = ane
        self.bufmngr = ane.bufmngr
        self.req_iova_base = None
        self.req_width = None
        return

    def set_nid_in_buf(self, td_buf, new_nid):
        assert ((new_nid > 0) and (new_nid < 0xff))
        hdr0 = TD_HDR0(struct.unpack('<L', td_buf[:4])[0])
        hdr0.NID = new_nid
        return struct.pack('<L', hdr0._value) + td_buf[4:]

    def init_req_fifo(self, cur_req):
        self.req_width = nextpow2(cur_req.size)
        self.req_iova_base = self.bufmngr.alloc_size(
            self.REQ_FIFO_COUNT * self.req_width)
        return

    def prep_nxt_req(self, cur_req, cur_nid=0x14):
        assert ((self.req_iova_base != None) and (self.req_width != None))
        assert ((cur_nid > 0) and (cur_nid < 0xff))
        nxt_nid = cur_nid + self.REQ_FIFO_COUNT
        assert ((nxt_nid > 0) and (nxt_nid < 0xff))

        cur_req.nid = cur_nid
        cur_td_buf = self.set_nid_in_buf(cur_req.ts.td_buf, cur_nid)
        nxt_td_buf = self.set_nid_in_buf(cur_req.ts.td_buf, nxt_nid)
        print('cur_nid: 0x%x, nxt_nid: 0x%x' % (cur_nid, nxt_nid))

        req_idx = 0  # TODO
        cur_req.iova = self.req_iova_base + req_idx*self.req_width
        nxt_req_iova = cur_req.iova + self.req_width
        self.ane.iowrite(cur_req.iova, cur_td_buf)
        self.ane.iowrite(nxt_req_iova, nxt_td_buf)
        return cur_req


class BAR:
    def __init__(self):
        self.ts   = 0
        self.krn  = 0
        self.p_2  = 0
        self.intm = 0
        self.dst  = 0
        self.src1 = 0
        self.src2 = 0
        self.p_7  = 0
        self.p_8  = 0
        self.p_9  = 0
        self.p_a  = 0
        self.p_b  = 0
        self.p_c  = 0
        self.p_d  = 0
        self.p_e  = 0
        self.p_f  = 0
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
