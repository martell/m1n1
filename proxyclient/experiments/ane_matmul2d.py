#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from m1n1.setup import *
from m1n1.shell import run_shell

import numpy as np

from m1n1.ane import ANE
from m1n1.ane.ane_tm import TaskManager
from m1n1.ane.ane_context import TaskSequence, ReqManager
from m1n1.ane.ane_utils import zero_pad, make_padding
from m1n1.ane.compiler.matmul2d import compile_matmul2d


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

def push2hw(req):
    print('pushing to hw...')
    (dma_r1, dma_w1, dma_rw1) = ane.get_dma_perf_stats()
    ane.get_timestamp()

    tm.enqueue_tq(req)
    tm.execute_tq(req)

    ane.get_timestamp()
    (dma_r2, dma_w2, dma_rw2) = ane.get_dma_perf_stats()
    print('perf: total: dma_r: 0x%x, dma_w: 0x%x, dma_rw: 0x%x' 
                                        % (dma_r2, dma_w2, dma_rw2))
    print('perf: delta: dma_r: 0x%x, dma_w: 0x%x, dma_rw: 0x%x' 
                                        % (dma_r2-dma_r1, dma_w2-dma_w1, 
                                           dma_rw2-dma_rw1))

    dst_buf = ane.ioread(req.bar.dst, ane.TILE_SIZE)
    return dst_buf


def main(src1_arr, src2_arr, compiler_args, dst_shape):
    ts_buf = compile_matmul2d(*compiler_args)
    ts_prop = [0x274, 0x274, 0x278, 0x278, 0x274] # TODO
    ts = TaskSequence(ts_buf, ts_prop)

    reqmngr.init_req(ts)
    prep_bufs(src1_arr, src2_arr)
    reqmngr.make_fifo_head() # push fifo
    dst_buf = push2hw(reqmngr.req)

    ref_arr = src1_arr @ src2_arr
    print('ref_arr: \n')
    print(ref_arr, '\n\n')
    print('drumroll pls .....')

    dst_arr = ane.tiler.tile2arr(dst_buf, dst_shape)
    print('dst_arr: \n')
    print(dst_arr, '\n\n')
    return dst_arr


M = 5 # HOLD
N = 32 # 1 <= N <= 1024
P = 16 # 1 <= P <= 16 # trails off weird past 16
src1_arr = np.random.rand(M*N).reshape((M, N)).astype(np.float64)
src2_arr = np.random.rand(N*P).reshape((N, P)).astype(np.float64)
main(src1_arr, src2_arr, (N, P), (M, P))
run_shell(globals(), msg="Have fun!")

