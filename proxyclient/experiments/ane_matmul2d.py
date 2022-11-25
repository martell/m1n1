#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from m1n1.setup import *
from m1n1.shell import run_shell

from m1n1.ane import ANE
from m1n1.ane.ane_tm import TaskManager
from m1n1.ane.ane_context import TaskSequence, ReqManager
from m1n1.ane.ane_utils import zero_pad, make_padding
from m1n1.ane.compiler.matmul2d import compile_matmul2d

import numpy as np

# userspace

M = 5 # HOLD
N = 8 # 1 <= N <= 500
P = 3 # HOLD
src1_arr = np.arange(M*N).reshape((M, N)).astype(np.float64)
src2_arr = np.arange(N*P).reshape((N, P)).astype(np.float64)

ts_buf = compile_matmul2d(N)
# open('compiled.bin', 'wb').write(ts_buf)
ts_prop = [0x274, 0x274, 0x278, 0x278, 0x274] # TODO
ts = TaskSequence(ts_buf, ts_prop)

# ----------------------------------

# init platform
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
reqmngr = ReqManager(ane)
reqmngr.init_req(ts)

def prep_bufs(src1_arr, src2_arr):
    src1_buf = zero_pad(ane.tiler.arr2tile(src1_arr), ane.TILE_SIZE)
    reqmngr.setup_src1(src1_buf)

    src2_buf = zero_pad(ane.tiler.arr2tile(src2_arr), ane.TILE_SIZE)
    reqmngr.setup_src2(src2_buf)

    krn_buf = make_padding(0x4000) # BAR filled regardless
    reqmngr.setup_krn(krn_buf)

    intm_buf = src1_buf # copy of src1 that gets broadcasted
    reqmngr.setup_intm(intm_buf)

    dst_buf = make_padding(ane.TILE_SIZE)
    reqmngr.setup_dst(dst_buf)
    return

prep_bufs(src1_arr, src2_arr)
reqmngr.make_fifo_head() # push fifo
# ane.bufmngr.dump_map()
# ane.bufmngr.dump_bufs()

# ----------------------------------

# lets goooo
def push2hw(req):
    print('\n\npushing to hw...')
    (dma_r1, dma_w1, dma_rw1) = ane.get_dma_perf_stats()

    dst_iova = req.bar.dst
    dst_buf_prev = ane.ioread(dst_iova, ane.TILE_SIZE)
    # open("prev.bin", "wb").write(dst_buf_prev)
    ane.get_timestamp()

    # these two are the actual pushes
    # everything else here is just sugar
    tm.enqueue_tq(req)
    tm.execute_tq(req)

    ane.get_timestamp()
    dst_buf_post = ane.ioread(dst_iova, ane.TILE_SIZE) # diff :)
    # open("post.bin", "wb").write(dst_buf_post)

    (dma_r2, dma_w2, dma_rw2) = ane.get_dma_perf_stats()
    print('perf: total: dma_r: 0x%x, dma_w: 0x%x, dma_rw: 0x%x' 
                                        % (dma_r2, dma_w2, dma_rw2))
    print('perf: delta: dma_r: 0x%x, dma_w: 0x%x, dma_rw: 0x%x' 
                                        % (dma_r2-dma_r1, dma_w2-dma_w1, 
                                           dma_rw2-dma_rw1))
    
    ref_arr = src1_arr @ src2_arr
    print('ref_arr: \n')
    print(ref_arr, '\n\n')
    print('drumroll pls .....')
    dst_arr = ane.tiler.tile2arr(dst_buf_post, (M, P))
    print('dst_arr: \n')
    print(dst_arr, '\n\n')

    print('shape eq: %r' % (dst_arr.shape == ref_arr.shape))
    print('arr eq: %r' % (np.array_equal(dst_arr, ref_arr)))
    print('\n')
    return dst_arr

# push2hw(reqmngr.req)


run_shell(globals(), msg="Have fun!")
