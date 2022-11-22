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
from m1n1.ane.td.conv import get_conv_dims, conv_2d_input_T

"""
simple 2D NCHW convolution

AVAILABLE PARAMS: 
input_size: 
    - aka H/W of NCHW
    - td_magic transform verified for 1 <= x <= 64
    - however tile overflows at 32, which 
        - enables dma interleave into 2 separate tiles
        - .. which i havent figured out, sigh
    - so hard cap 1 <= input_size <= 32

alpha, beta:
    - ufloat quart values to populate src, krn arr resp.
        - haven't tested for non-uniform mats
    - getting weird rounding errors below 2**-2
    - packed floats also trail off past 1024
    - so float packing is capped to 250*4 = 1000 for now
        - so soft cap:
            - 0.25 <= alpha <= 8.00
            - 0.25 <= beta <= 7.75
        - to account for dst (8 * 7.75 * 4 = 248)


curl -LJO https://raw.githubusercontent.com/seanlatias/tvm/59512007e49ebb0d8080b38465e93c241b13413c/topi/python/topi/testing/conv2d_nchw_python.py 
into ane/td/ to enable testing

"""

DBG_CFG_REGMON_ON = 1
DBG_CFG_SHELL_RUN = 1
DBG_CFG_CONV_TEST = 1

if DBG_CFG_CONV_TEST:
    from m1n1.ane.td.conv2d_nchw_python import conv2d_nchw_python

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
krn_iova = 0x1fc0280 # td_iova + len(td_buf) roundedup
req_iova_base = 0x1fc8000 # fifo
src_iova = 0x1fd8000 
dst_iova = 0x1fe0000 # 0x1fe4000 if src tile overflow

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
                        p_dst=dst_iova, p_src1=src_iova))
    
    # dst_buf_prev = ane.ioread(dst_iova, ane.TILE_SIZE)
    ane.get_timestamp()
    tm.enqueue_tq(task, queue_id=queue_id)
    tm.execute_tq()
    ane.get_timestamp()
    # dst_buf_post = ane.ioread(dst_iova, ane.TILE_SIZE) # diff :)
    return

# ---------------------------------------------

def main(input_size, alpha, beta, 
            req_idx=0, cur_nid=0x15, queue_id=4):
    (dma_r1, dma_w1, dma_rw1) = ane.get_dma_perf_stats()

    input_dim, weight_dim, output_dim = get_conv_dims(input_size=input_size)
    td_buf = lz_pack(conv_2d_input_T(input_size))
    ane.iowrite(td_iova, td_buf)
    
    src_arr = np.zeros(input_dim) + alpha
    src_buf = zero_pad(ane.tiler.arr2tile(src_arr), ane.TILE_SIZE)
    ane.iowrite(src_iova, src_buf)

    krn_arr = np.zeros(weight_dim) + beta
    krn_buf = zero_pad(ane.tiler.arr2krn(krn_arr), 0x40) # TODO derive 
    ane.iowrite(krn_iova, krn_buf)

    # lets gooo
    push2hw(td_buf, req_idx, cur_nid, queue_id)
    dst_buf = ane.ioread(dst_iova, ane.TILE_SIZE)
    dst_arr = ane.tiler.tile2arr(dst_buf, output_dim)

    if DBG_CFG_CONV_TEST:
        ref_arr = conv2d_nchw_python(src_arr, krn_arr, 
                                        stride=1, padding='VALID')
        if not (np.array_equal(dst_arr, ref_arr)):
            raise ValueError ('uh oh, good luck')

    (dma_r2, dma_w2, dma_rw2) = ane.get_dma_perf_stats()
    print('perf: total: dma_r: 0x%x, dma_w: 0x%x, dma_rw: 0x%x' 
                                        % (dma_r2, dma_w2, dma_rw2))
    print('perf: delta: dma_r: 0x%x, dma_w: 0x%x, dma_rw: 0x%x' 
                                        % (dma_r2-dma_r1, dma_w2-dma_w1, dma_rw2-dma_rw1))
    return dst_arr


def full_poc():
    """
    if you do choose to run this:
    it does feel *slightly* warmer
    and you can guess the state of pmgmt rn
    so i suggest cooling down / rebooting into macos
    """
    alphas = np.linspace(0.25, 8.00, int(8.00*4))
    betas = np.linspace(0.25, 7.75, int(7.75*4))
    input_sizes = np.arange(1, 32 + 1)

    for alpha in alphas:
        for beta in betas:
            for input_size in input_sizes:
                main(input_size=input_size, alpha=alpha, beta=beta)
                time.sleep(0.05)
    return


main(input_size=1, alpha=0.25, beta=0.25, queue_id=np.random.randint(1, 7))
main(input_size=32, alpha=8.00, beta=7.75, queue_id=np.random.randint(1, 7))


if DBG_CFG_SHELL_RUN:
    run_shell(globals(), msg="Have fun!")
