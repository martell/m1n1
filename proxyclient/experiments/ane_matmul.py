#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from m1n1.setup import *
from m1n1.shell import run_shell

import numpy as np

from m1n1.ane import ANE
from m1n1.ane.ane_tm import TaskManager
from m1n1.ane.ane_td import Task, set_nid_in_buf
from m1n1.ane.ane_utils import *


DBG_CFG_REGMON_ON = 1
DBG_CFG_SHELL_RUN = 1

ane = ANE(u)
ane.powerup()

if DBG_CFG_REGMON_ON:
    rnges = [(0x26b900000, 0x26b90c1fc, 'perf'),
            (0x26bc04000, 0x26bc28000, 'ane'),]
    mon = RegMonitor(u)
    for (start, end, name) in rnges:
        mon.add(start, end-start, name=name)
    mon.poll() # should work after ane.powerup()

tm = TaskManager(ane, 0x26bc00000) # TODO other boards ?
tm.init_tqs()

if DBG_CFG_REGMON_ON:
    mon.poll()

# ---------------------------------------------

ane.init_vmem_region()

req_iova_base = 0x1fcc000

# in BAR order:
td_iova = 0x1fc0000
krn_iova = 0x1fc0e80 # written in BAR regardless
intm_iova = 0x1fdc000 # type2, copy of src1
src_iova2 = 0x1ff4000
src_iova1 = 0x1fe4000
dst_iova = 0x1fec000

td_buf_all = open('m1n1/ane/compiler/matmul.bin', 'rb').read() # 0xe74
ane.iowrite(td_iova, td_buf_all)
td_buf = td_buf_all[:0x274] # first td; 0x274
td_count = 5 # TODO derive

# make input bufs
M = 5
N = 8
P = 3
input_shape1 = (M, N)
input_shape2 = (N, P)

src_arr1 = np.arange(M*N).reshape((M,N)).astype(np.float64)
src_arr2 = np.arange(N*P).reshape((N,P)).astype(np.float64)
src_buf1 = zero_pad(ane.tiler.arr2tile(src_arr1), ane.TILE_SIZE)
src_buf2 = zero_pad(ane.tiler.arr2tile(src_arr2), ane.TILE_SIZE)
ane.iowrite(src_iova1, src_buf1)
ane.iowrite(src_iova2, src_buf2)

intm_buf = src_buf1 # ???
ane.iowrite(intm_iova, intm_buf)

krn_buf = make_padding(0x4000) # ??
ane.iowrite(krn_iova, krn_buf)

# ---------------------------------------------

def push2hw(td_buf, req_idx=1, cur_nid=0x4, queue_id=4):
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

    task = Task(dict(nid=cur_nid, req_iova=cur_req_iova, 
                        size=td_size, count=td_count))
    task.setup_BAR(dict(p_head=td_iova, p_krn=krn_iova, 
                        p_intm=intm_iova, p_dst=dst_iova,
                        p_src1=src_iova1, p_src2=src_iova2))
    
    dst_buf_prev = ane.ioread(dst_iova, ane.TILE_SIZE)
    
    ane.get_timestamp()
    tm.enqueue_tq(task, queue_id=queue_id)
    tm.execute_tq()
    ane.get_timestamp()
    dst_buf_post = ane.ioread(dst_iova, ane.TILE_SIZE) # diff :)
    return



if DBG_CFG_SHELL_RUN:
    run_shell(globals(), msg="Have fun!")

