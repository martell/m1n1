#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from m1n1.setup import *
from m1n1.shell import run_shell

from m1n1.ane import ANE
from m1n1.ane.ane_tm import TaskManager
from m1n1.ane.ane_context import ReqManager, EngineReq
from m1n1.ane.ane_utils import *

import numpy as np

M = 5
N = 8
P = 3
src_arr1 = np.arange(M*N).reshape((M, N)).astype(np.float64)
src_arr2 = np.arange(N*P).reshape((N, P)).astype(np.float64)

# ----------------------------------

ane = ANE(u)
ane.powerup()

DBG_CFG_REGMON_ON = 1
if DBG_CFG_REGMON_ON:
    rnges = [(0x26b900000, 0x26b90c1fc, 'perf'),
            (0x26bc04000, 0x26bc28000, 'ane'),]
    mon = RegMonitor(u)
    for (start, end, name) in rnges:
        mon.add(start, end-start, name=name)
    mon.poll() # should work after ane.powerup()

tm = TaskManager(ane, 0x26bc00000) # TODO other boards ?
tm.init_tqs()

# ----------------------------------

src_buf1 = zero_pad(ane.tiler.arr2tile(src_arr1), ane.TILE_SIZE)
src_buf2 = zero_pad(ane.tiler.arr2tile(src_arr2), ane.TILE_SIZE)
src_iova1 = ane.bufmngr.alloc_buf(src_buf1)
src_iova2 = ane.bufmngr.alloc_buf(src_buf2)

krn_iova = ane.bufmngr.alloc_size(0x4000) # still allocs size?
intm_buf = src_buf1 # copy of src1 that gets broadcasted
intm_iova = ane.bufmngr.alloc_buf(intm_buf) 
dst_iova = ane.bufmngr.alloc_size(ane.TILE_SIZE)

ane.bufmngr.run_syncttbr()
ane.bufmngr.dump_bufs()

# ----------------------------------

# WIP
ts_buf = open("m1n1/ane/compiler/matmul.bin", 'rb').read()
ts_prop = [0x274, 0x274, 0x278, 0x278, 0x274]

req = EngineReq(ts_buf, ts_prop)
ts_iova = ane.bufmngr.alloc_buf(req.ts.ts_buf)
req.setup_BAR(dict( ts=ts_iova, krn=krn_iova, 
                    intm=intm_iova, dst=dst_iova,
                    src1=src_iova1, src2=src_iova2 ))

reqmngr = ReqManager(ane, req)
reqmngr.prep_nxt_req(req)

# ----------------------------------

def push2hw():
    (dma_r1, dma_w1, dma_rw1) = ane.get_dma_perf_stats()
    dst_buf_prev = ane.ioread(dst_iova, ane.TILE_SIZE)
    open('prev.bin', 'wb').write(dst_buf_prev)
    ane.get_timestamp()

    tm.enqueue_tq(req)
    tm.execute_tq(req)

    ane.get_timestamp()
    dst_buf_post = ane.ioread(dst_iova, ane.TILE_SIZE) # diff :)
    open('post.bin', 'wb').write(dst_buf_post)

    dst_arr = ane.tiler.tile2arr(dst_buf_post, (M, P))
    (dma_r2, dma_w2, dma_rw2) = ane.get_dma_perf_stats()
    print('perf: total: dma_r: 0x%x, dma_w: 0x%x, dma_rw: 0x%x' 
                                        % (dma_r2, dma_w2, dma_rw2))
    print('perf: delta: dma_r: 0x%x, dma_w: 0x%x, dma_rw: 0x%x' 
                                        % (dma_r2-dma_r1, dma_w2-dma_w1, 
                                           dma_rw2-dma_rw1))
    return dst_arr

# push2hw()


run_shell(globals(), msg="Have fun!")
