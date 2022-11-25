#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from m1n1.setup import *
from m1n1.shell import run_shell

import numpy as np

from m1n1.ane import ANE
from m1n1.ane.ane_tm import TaskManager
from m1n1.ane.ane_context import ReqManager, EngineReq
from m1n1.ane.ane_utils import *
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

reqmngr = ReqManager(ane)

# ---------------------------------------------


def prep_input(src_arr1, src_arr2):
    assert(src_arr1.shape == src_arr2.shape)
    M = len(src_arr1)

    # compile
    ts_buf = compile_elemwise1d(M)
    # open('compiled.bin', 'wb').write(ts_buf)
    ts_prop = [len(ts_buf)] # non-chained, so only 1

    # tile bufs
    src_buf1 = zero_pad(ane.tiler.arr2tile(src_arr1), ane.TILE_SIZE)
    src_buf2 = zero_pad(ane.tiler.arr2tile(src_arr2), ane.TILE_SIZE)
    src1_bufid = ane.bufmngr.alloc_buf(src_buf1)
    src_iova2 = ane.bufmngr.alloc_buf(src_buf2)
    
    krn_iova = ane.bufmngr.alloc_size(0x4000) # still allocs empty
    intm_iova = 0 # none
    dst_iova = ane.bufmngr.alloc_size(ane.TILE_SIZE)
    ane.bufmngr.run_syncttbr()
    # ane.bufmngr.dump_bufmap()
    # ane.bufmngr.dump_bufs()

    # make req
    req = EngineReq(ts_buf, ts_prop)
    ts_iova = ane.bufmngr.alloc_buf(req.ts.ts_buf)
    req.setup_BAR(dict( ts=ts_iova, krn=krn_iova, 
                        intm=intm_iova, dst=dst_iova,
                        src1=src_iova1, src2=src_iova2 ))

    
    reqmngr.prep_nxt_req(req)
    return


# ---------------------------------------------

mode_ref_lambdas = {'ADD': lambda A, B: A + B, 
                    'MULT': lambda A, B: A * B,
                    'MAX': lambda A, B: np.maximum(A, B),
                    'MIN': lambda A, B: np.minimum(A, B)}

def main(src_arr1, src_arr2, mode):
    assert(isinstance(src_arr1, (np.ndarray, np.generic)))
    assert(isinstance(src_arr2, (np.ndarray, np.generic)))
    assert(src_arr1.shape == src_arr2.shape)
    assert(src_arr1.ndim == 1)

    (dma_r1, dma_w1, dma_rw1) = ane.get_dma_perf_stats()

    input_size = len(src_arr1)
    assert(1 <= input_size <= 0x2000)
    input_dim, output_dim = (input_size,), (input_size,)
    
    td_buf = ez_pack(elemwise_transform(input_size, mode))
    ane.iowrite(td_iova, td_buf)

    src_buf1 = zero_pad(ane.tiler.arr2tile(src_arr1), ane.TILE_SIZE)
    ane.iowrite(src_iova1, src_buf1)
    src_buf2 = zero_pad(ane.tiler.arr2tile(src_arr2), ane.TILE_SIZE)
    ane.iowrite(src_iova2, src_buf2)

    # lets gooo
    push2hw(td_buf)
    dst_buf = ane.ioread(dst_iova, ane.TILE_SIZE)
    dst_arr = ane.tiler.tile2arr(dst_buf, output_dim)

    ref_arr = mode_ref_lambdas[mode](src_arr1, src_arr2)
    # if not (np.array_equal(dst_arr, ref_arr)):
        # raise ValueError ('uh oh, good luck')
    print(dst_arr, ref_arr)
    (dma_r2, dma_w2, dma_rw2) = ane.get_dma_perf_stats()
    print('perf: total: dma_r: 0x%x, dma_w: 0x%x, dma_rw: 0x%x' 
                                        % (dma_r2, dma_w2, dma_rw2))
    print('perf: delta: dma_r: 0x%x, dma_w: 0x%x, dma_rw: 0x%x' 
                                        % (dma_r2-dma_r1, dma_w2-dma_w1, dma_rw2-dma_rw1))
    return dst_arr


M = 4000
src_arr1 = np.random.rand(M) * 6.626
src_arr2 = np.random.rand(M) * 3.1415 
dst_arr = main(src_arr1=src_arr1, src_arr2=src_arr2, mode='ADD')

M = 1
src_arr1 = np.random.rand(M) * 6.022
src_arr2 = np.random.rand(M) * 2.71828182
dst_arr = main(src_arr1=src_arr1, src_arr2=src_arr2, mode='MULT')

M = 64
src_arr1 = np.random.rand(M) * 2021
src_arr2 = np.random.rand(M) * 2022
dst_arr = main(src_arr1=src_arr1, src_arr2=src_arr2, mode='MAX')

M = 3333
src_arr1 = np.random.rand(M)
src_arr2 = np.random.rand(M)
dst_arr = main(src_arr1=src_arr1, src_arr2=src_arr2, mode='MIN')


if DBG_CFG_SHELL_RUN:
    run_shell(globals(), msg="Have fun!")
