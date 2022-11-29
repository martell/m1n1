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
from m1n1.ane.compiler.conv2d import get_conv2d_dims, compile_conv2d


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

tm = TaskManager(ane)
tm.init_tqs()

# ----------------------------------

reqmngr = ReqManager(ane)

def prep_bufs(src1_arr, krn_arr):
    src1_buf = zero_pad(ane.tiler.arr2tile(src1_arr), ane.TILE_SIZE)
    reqmngr.setup_src1(src1_buf)

    src2_buf = None
    reqmngr.setup_src2(src2_buf)

    krn_buf = ane.tiler.arr2krn(krn_arr)
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


def main(src_arr, krn_arr, output_dim):
    N, C, H, W = src_arr.shape
    ts_buf = compile_conv2d(H)
    ts_prop = [len(ts_buf)]
    ts = TaskSequence(ts_buf, ts_prop)

    reqmngr.init_req(ts)
    prep_bufs(src_arr, krn_arr)
    reqmngr.make_fifo_head() # push fifo
    dst_buf = push2hw(reqmngr.req)

    dst_arr = ane.tiler.tile2arr(dst_buf, output_dim)
    print('dst_arr: \n')
    print(dst_arr, '\n\n')
    return dst_arr


H = 32
input_dim, weight_dim, output_dim = get_conv2d_dims(input_size=H)
src_arr = np.zeros(input_dim) + 3.1415
krn_arr = np.zeros(weight_dim) + 6.626
dst_arr = main(src_arr, krn_arr, output_dim)

run_shell(globals(), msg="Have fun!")
