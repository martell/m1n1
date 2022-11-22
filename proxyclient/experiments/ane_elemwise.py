#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from m1n1.setup import *
from m1n1.shell import run_shell

import numpy as np

from m1n1.ane import ANE
from m1n1.ane.ane_tm import TaskManager
from m1n1.ane.ane_task import Task
from m1n1.ane.ane_utils import *
from m1n1.ane.td.hdr import set_nid_in_buf
from m1n1.ane.td.elemwise import elemwise_1d_T

"""
1D element-wise ADD/MULTIPLY/MAX/MIN

input1: (M,)
input2: (M,)
output: (M,)

1 <= M <= 4000 # got bored after lol
min(arr) >= 0.25 && max(arr) <= 250
"""

DBG_CFG_REGMON_ON = 1
DBG_CFG_SHELL_RUN = 1

ane = ANE(u)
ane.powerup()

if DBG_CFG_REGMON_ON:
    rnges = [
            (0x26b900000, 0x26b90c1fc, 'perf'),
            (0x26bc04000, 0x26bc28000, 'ane'),
            ]
    mon = RegMonitor(u)
    for (start, end, name) in rnges:
        mon.add(start, end-start, name=name)
    mon.poll() # should work after ane.powerup()

tm = TaskManager(ane, 0x26bc00000) # TODO other boards ?
tm.init_tqs()

if DBG_CFG_REGMON_ON:
    mon.poll()

# ---------------------------------------------

def map_dart_vmem_region(ane, vmem_start, vmem_end):
    for iova in range(vmem_start, vmem_end, ane.PAGE_SIZE):
        phys = ane.u.memalign(ane.PAGE_SIZE, ane.PAGE_SIZE)
        ane.p.memset32(phys, 0, ane.PAGE_SIZE)
        ane.dart.iomap_at(0, iova, phys, ane.PAGE_SIZE)
    return

# mem management is nonexistent rn
# similar to what macos allocs:

td_iova = 0x1fc0000
# even though kernel is nonexistent in
# elemwise mode, it's still written in BAR
krn_iova = 0x1fc0280 # td_iova + len(td_buf) roundedup
req_iova_base = 0x1fcc000 # - 0x1fd0000; fifo
src_iova1 = 0x1fdc000
src_iova2 = 0x1fe4000
dst_iova = 0x1fec000

# map around work region
map_dart_vmem_region(ane, 0x1fa0000, 0x1ff0000)
ane.syncttbr() 
print('vmem region initialized.')

# ---------------------------------------------

def push2hw(td_buf, req_idx=0, cur_nid=0x15, queue_id=4):
    """
    push to hw after bufs are written
    """
    td_size = len(td_buf) # 0x274
    req_width = nextpow2(td_size) # 0x400

    assert((cur_nid > 0) and (cur_nid < 0xff))
    # TODO: calculate from hdr nxt offset
    nxt_nid = cur_nid + 0x20
    assert((nxt_nid > 0) and (nxt_nid < 0xff))
    cur_td_buf = set_nid_in_buf(td_buf, cur_nid)
    nxt_td_buf = set_nid_in_buf(td_buf, nxt_nid)
    print('cur_nid: 0x%x, nxt_nid: 0x%x' % (cur_nid, nxt_nid))

    cur_req_iova = req_iova_base + req_idx*req_width
    nxt_req_iova = cur_req_iova + req_width
    ane.iowrite(cur_req_iova, cur_td_buf)
    ane.iowrite(nxt_req_iova, nxt_td_buf)

    task = Task(nid=cur_nid, req_iova=cur_req_iova, size=td_size)
    task.setup_BAR(dict(p_head=td_iova, p_krn=krn_iova, 
                        p_dst=dst_iova, p_src1=src_iova1, p_src2=src_iova2))
    
    # dst_buf_prev = ane.ioread(dst_iova, ane.TILE_SIZE)
    ane.get_timestamp()
    tm.enqueue_tq(task, queue_id=queue_id)
    tm.execute_tq()
    ane.get_timestamp()
    # dst_buf_post = ane.ioread(dst_iova, ane.TILE_SIZE) # diff :)
    return

# ---------------------------------------------

mode_ref_lambdas = {'ADD': lambda A, B: A + B, 
                    'MULTIPLY': lambda A, B: A * B,
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
    
    td_buf = lz_pack(elemwise_1d_T(input_size, mode))
    ane.iowrite(td_iova, td_buf)

    src_buf1 = zero_pad(ane.tiler.arr1d2tile(src_arr1), ane.TILE_SIZE)
    ane.iowrite(src_iova1, src_buf1)
    src_buf2 = zero_pad(ane.tiler.arr1d2tile(src_arr2), ane.TILE_SIZE)
    ane.iowrite(src_iova2, src_buf2)

    # lets gooo
    push2hw(td_buf)
    dst_buf = ane.ioread(dst_iova, ane.TILE_SIZE)
    dst_arr = ane.tiler.tile2arr1d(dst_buf, output_dim)

    ref_arr = mode_ref_lambdas[mode](src_arr1, src_arr2)
    if not (np.array_equal(dst_arr, ref_arr)):
        raise ValueError ('uh oh, good luck')


    (dma_r2, dma_w2, dma_rw2) = ane.get_dma_perf_stats()
    print('perf: total: dma_r: 0x%x, dma_w: 0x%x, dma_rw: 0x%x' 
                                        % (dma_r2, dma_w2, dma_rw2))
    print('perf: delta: dma_r: 0x%x, dma_w: 0x%x, dma_rw: 0x%x' 
                                        % (dma_r2-dma_r1, dma_w2-dma_w1, dma_rw2-dma_rw1))
    return dst_arr


M = 20
src_arr1 = np.linspace(0.25, M, M*4)[:M]
src_arr2 = np.linspace(0.25, M, M*4)[:M]
dst_arr = main(src_arr1=src_arr1, src_arr2=src_arr2, mode='ADD')
print(src_arr1, src_arr2, dst_arr)

M = 4000
src_arr1 = np.zeros((M,)) + 2.00
src_arr2 = np.zeros((M,)) + 3.50
dst_arr = main(src_arr1=src_arr1, src_arr2=src_arr2, mode='MULTIPLY')
print(src_arr1, src_arr2, dst_arr)

M = 64
src_arr1 = np.linspace(0.25, M, M*4)[:M]
np.random.shuffle(src_arr1)
src_arr2 = np.linspace(0.25, M, M*4)[:M]
np.random.shuffle(src_arr2)
dst_arr = main(src_arr1=src_arr1, src_arr2=src_arr2, mode='MAX')
print(src_arr1, src_arr2, dst_arr)

M = 8
src_arr1 = np.linspace(0.25, M, M*4)[:M]
np.random.shuffle(src_arr1)
src_arr2 = np.linspace(0.25, M, M*4)[:M]
np.random.shuffle(src_arr2)
dst_arr = main(src_arr1=src_arr1, src_arr2=src_arr2, mode='MIN')
print(src_arr1, src_arr2, dst_arr)


if DBG_CFG_SHELL_RUN:
    run_shell(globals(), msg="Have fun!")
