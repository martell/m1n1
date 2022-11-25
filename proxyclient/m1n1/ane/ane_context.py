# SPDX-License-Identifier: MIT

import os
import struct
from datetime import datetime
from dataclasses import dataclass

from m1n1.hw.ane import TD_HDR0
from m1n1.ane.ane_utils import roundup, nextpow2, make_padding


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
        self.alloc_size(0x4000) # for the sake of sync
        self.run_syncttbr()
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
        return buf.vaddr

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
        return buf.vaddr

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
        os.makedirs(outdir, exist_ok=True)
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
        self.td_count = len(self.ts_prop)
        
        # t0: head td that populates fifo req pool
        self.t0_buf = self.ts_buf[:self.ts_prop[0]]
        self.t0_size = len(self.t0_buf)
        return


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


@dataclass 
class EngineReq: # hardware req struct
    td_buf: bytes # for fifo
    td_size: int 
    td_count: int
    vaddr: int = 0
    nid: int = 0
    bar: BAR = BAR()


class ReqManager:

    FIFO_COUNT = 0x20

    def __init__(self, ane):
        self.ane = ane
        self.req = None
        self.fifo_width = None
        self.fifo_base = None
        self.fifo_idx = 0
        return
    
    def init_req(self, ts):
        self.req = EngineReq(td_buf=ts.t0_buf, 
                            td_size=ts.t0_size, td_count=ts.td_count)
        # alloc fifo region
        self.fifo_width = nextpow2(self.req.td_size)
        self.fifo_base = self.ane.bufmngr.alloc_size(
            self.FIFO_COUNT * self.fifo_width)
        
        self.setup_ts(ts.ts_buf)
        return

    def assign_nid(self):
        # TODO schedule from fifo availability
        # rn just gives any 0 < x < 0xff - FIFO_COUNT
        return 0x23 

    def set_nid_in_td_buf(self, td_buf, new_nid):
        assert ((new_nid > 0) and (new_nid < 0xff))
        hdr0 = TD_HDR0(struct.unpack('<L', td_buf[:4])[0])
        hdr0.NID = new_nid
        return struct.pack('<L', hdr0._value) + td_buf[4:]

    def make_fifo_head(self):
        assert ((self.fifo_base != None) and (self.fifo_width != None))
        
        cur_nid = self.assign_nid()
        assert ((cur_nid > 0) and (cur_nid < 0xff))
        nxt_nid = cur_nid + self.FIFO_COUNT
        assert ((nxt_nid > 0) and (nxt_nid < 0xff))
        self.req.nid = cur_nid

        cur_td_buf = self.set_nid_in_td_buf(self.req.td_buf, cur_nid)
        nxt_td_buf = self.set_nid_in_td_buf(self.req.td_buf, nxt_nid)
        print('cur_nid: 0x%x, nxt_nid: 0x%x' % (cur_nid, nxt_nid))

        self.req.vaddr = self.fifo_base + self.fifo_idx*self.fifo_width
        nxt_req_iova = self.req.vaddr + self.fifo_width
        self.ane.iowrite(self.req.vaddr, cur_td_buf)
        self.ane.iowrite(nxt_req_iova, nxt_td_buf) # necessary?
        return

    def setup_ts(self, ts_buf):
        self.req.bar.ts = self.ane.bufmngr.alloc_data(ts_buf)
        return

    def setup_src1(self, src1_buf):
        assert(not len(src1_buf) % self.ane.TILE_SIZE)
        self.req.bar.src1 = self.ane.bufmngr.alloc_data(src1_buf)
        return

    def setup_src2(self, src2_buf):
        if (src2_buf == None): return
        assert(not len(src2_buf) % self.ane.TILE_SIZE)
        self.req.bar.src2 = self.ane.bufmngr.alloc_data(src2_buf)
        return

    def setup_krn(self, krn_buf):
        self.req.bar.krn = self.ane.bufmngr.alloc_data(krn_buf)
        return

    def setup_intm(self, intm_buf):
        if (intm_buf == None): return
        self.req.bar.intm = self.ane.bufmngr.alloc_data(intm_buf)
        return

    def setup_dst(self, dst_buf):
        assert(not len(dst_buf) % self.ane.TILE_SIZE)
        self.req.bar.dst = self.ane.bufmngr.alloc_data(dst_buf)
        return
