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
from m1n1.ane.compiler.elemwise1d import compile_elemwise1d

"""
1D element-wise ADD/MUL/MIN/MAX

input1: (M,)
input2: (M,)
output: (M,)
where 1 <= M <= 4000 // got bored after lol

"""

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

    intm_buf = None
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

# ----------------------------------

mode_ref = {
            'ADD': lambda A, B: A + B, 
            'MUL': lambda A, B: A * B,
            'MAX': lambda A, B: np.maximum(A, B),
            'MIN': lambda A, B: np.minimum(A, B)}

def main(src1_arr, src2_arr, mode):
    assert(src1_arr.shape == src2_arr.shape)
    assert(src1_arr.ndim == 1)
    M = len(src1_arr)

    ts_buf = compile_elemwise1d(M, mode)
    ts_prop = [len(ts_buf)]
    ts = TaskSequence(ts_buf, ts_prop)

    reqmngr.init_req(ts)
    prep_bufs(src1_arr, src2_arr)
    reqmngr.make_fifo_head() # push fifo
    dst_buf = push2hw(reqmngr.req)

    ref_arr = mode_ref[mode](src1_arr, src2_arr)
    print('ref_arr: \n')
    print(ref_arr, '\n\n')
    dst_arr = ane.tiler.tile2arr(dst_buf, (M,))
    print('dst_arr: \n')
    print(dst_arr, '\n\n')
    return dst_arr


M = 4000
src1_arr = np.random.rand(M) * 6.626
src2_arr = np.random.rand(M) * 3.1415 
dst_arr = main(src1_arr, src2_arr, mode='ADD')

M = 1
src1_arr = np.random.rand(M) * 6.022
src2_arr = np.random.rand(M) * 2.71828182
dst_arr = main(src1_arr, src2_arr, mode='MUL')

M = 64
src1_arr = np.random.rand(M) * 2021
src2_arr = np.random.rand(M) * 2022
dst_arr = main(src1_arr, src2_arr, mode='MAX')

M = 3333
src1_arr = np.random.rand(M)
src2_arr = np.random.rand(M)
dst_arr = main(src1_arr, src2_arr, mode='MIN')


run_shell(globals(), msg="Have fun!")
