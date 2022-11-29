# SPDX-License-Identifier: MIT

from m1n1.hw.ane import ANEDARTRegs


"""
ane has a single dart adt node but 4 reg instances.
0th is the actual dart base w/ config info (standard).

for whatever reason 1st & 2nd aren't dart bases but needs 
to (almost) mirror 0th, e.g. have to manually sync ttbr0.

3rd is base addr for random tunables + endpoint mappings 
for inter-process (e.g. shared server w/ isp) stuff in macos.
so it doesn't really matter (but still filled in jic).

also the values traced vs. adt values differ ever so slightly
that i can't tell if theyre actually using it. 
"""


def init_ane_dart_regs(ane):
    dart_regs_all = []
    for instance in range(3):
        dart_addr = ane.u.adt['/arm-io/dart-ane'].get_reg(instance)[0]
        print('instance: %d, dart_addr: 0x%x' % (instance, dart_addr))
        dart_regs_all.append(ANEDARTRegs(ane.u, dart_addr))

    # ane.p.dapf_init("/arm-io/dart-ane")
    # return dart_regs_all

    for instance in range(3):
        dart_regs_all[instance].ENABLED_STREAMS.val = 0x0  # disable

    if 1:
        dart_regs_all[0].ENABLED_STREAMS.val = 0x0
        dart_regs_all[0].TTBR[0, 0].val = 0x0
        dart_regs_all[0].TTBR[13, 0].val = 0x0
        dart_regs_all[0].TTBR[15, 0].val = 0x0
        dart_regs_all[0].STREAM_SELECT.val = 0xffffffff
        dart_regs_all[0].STREAM_COMMAND.val = 0x100000

    apply_ane_dart_tunables(ane)

    dart_regs_all[0].TCR[0].val = 0x80
    dart_regs_all[0].TCR[13].val = 0x100
    dart_regs_all[0].TCR[15].val = 0x100

    if 1:
        for instance in [1, 2]:
            dart_regs_all[instance].ENABLED_STREAMS.val = 0x0
            dart_regs_all[instance].TTBR[0, 0].val = 0x0
            dart_regs_all[instance].TTBR[13, 0].val = 0x0
            dart_regs_all[instance].TTBR[15, 0].val = 0x0
            dart_regs_all[instance].STREAM_SELECT.val = 0xffffffff
            dart_regs_all[instance].STREAM_COMMAND.val = 0x100000
            dart_regs_all[instance].CONFIG.val = 0x80016100
            dart_regs_all[instance].UNK_CONFIG_68.val = 0xf0f0f
            dart_regs_all[instance].UNK_CONFIG_6c.val = 0x80808

    dart_regs_all[1].TCR[0].val = 0x80
    dart_regs_all[1].TCR[13].val = 0x80000
    dart_regs_all[1].TCR[15].val = 0x20000

    dart_regs_all[2].TCR[0].val = 0x80
    dart_regs_all[2].TCR[13].val = 0x100
    dart_regs_all[2].TCR[15].val = 0x100

    for instance in range(3):
        dart_regs_all[instance].ENABLED_STREAMS.val = 0x1  # enable

    return dart_regs_all


"""
dart tunables mystery pt1: dart-tunables-instance-0,1,2

[(0x60, 0x4, 0x80006100),
 (0x0, 0x80006100, 0x0),
 (0x68, 0x4, 0xf0f0f),
 (0x0, 0xf0f0f, 0x0),
 (0x6c, 0x4, 0xffffff),
 (0x0, 0x80808, 0x0)]

vs.

[cpu2] [0xfffffe001387b1c0] MMIO: W.4   0x26b820060 (ane[0], offset 0x1820060) = 0x80016100
[cpu2] [0xfffffe0014093e3c] MMIO: R.4   0x26b820068 (ane[0], offset 0x1820068) = 0x20202
[cpu2] [0xfffffe001387b1c0] MMIO: W.4   0x26b820068 (ane[0], offset 0x1820068) = 0xf0f0f
[cpu2] [0xfffffe0014093e3c] MMIO: R.4   0x26b82006c (ane[0], offset 0x182006c) = 0x0
[cpu2] [0xfffffe001387b1c0] MMIO: W.4   0x26b82006c (ane[0], offset 0x182006c) = 0x80808
"""


"""
dart tunables mystery pt2: filter-data-instance-0

[(0x824000, 0x8, 0x8c7fff),
 (0x8, 0x10100, 0x1),
 (0x0, 0xf, 0xffffffff),
 (0xf, 0x30300, 0x1),
 (0x2b45c000, 0x2, 0x2b45c003),
 (0x2, 0x10300, 0x1),
 (0x3b70c000, 0x2, 0x3b70c033),
 (0x2, 0x10300, 0x1)]

vs. 

[cpu2] [0xfffffe001387b1a8] MMIO: W.4   0x26b804004 (ane[0], offset 0x1804004) = 0x1
[cpu2] [0xfffffe001387b1a8] MMIO: W.4   0x26b804008 (ane[0], offset 0x1804008) = 0x824000
[cpu2] [0xfffffe001387b1a8] MMIO: W.4   0x26b80400c (ane[0], offset 0x180400c) = 0x8
[cpu2] [0xfffffe001387b1a8] MMIO: W.4   0x26b804010 (ane[0], offset 0x1804010) = 0x8c7fff
[cpu2] [0xfffffe001387b1a8] MMIO: W.4   0x26b804014 (ane[0], offset 0x1804014) = 0x8
[cpu2] [0xfffffe001387b1a8] MMIO: W.4   0x26b804000 (ane[0], offset 0x1804000) = 0x11
[cpu2] [0xfffffe001387b1a8] MMIO: W.4   0x26b804044 (ane[0], offset 0x1804044) = 0x1
[cpu2] [0xfffffe001387b1a8] MMIO: W.4   0x26b804048 (ane[0], offset 0x1804048) = 0x0
[cpu2] [0xfffffe001387b1a8] MMIO: W.4   0x26b80404c (ane[0], offset 0x180404c) = 0xf
[cpu2] [0xfffffe001387b1a8] MMIO: W.4   0x26b804050 (ane[0], offset 0x1804050) = 0xffffffff
[cpu2] [0xfffffe001387b1a8] MMIO: W.4   0x26b804054 (ane[0], offset 0x1804054) = 0xf
[cpu2] [0xfffffe001387b1a8] MMIO: W.4   0x26b804040 (ane[0], offset 0x1804040) = 0x33
[cpu2] [0xfffffe001387b1a8] MMIO: W.4   0x26b804084 (ane[0], offset 0x1804084) = 0x1
[cpu2] [0xfffffe001387b1a8] MMIO: W.4   0x26b804088 (ane[0], offset 0x1804088) = 0x2b45c000
[cpu2] [0xfffffe001387b1a8] MMIO: W.4   0x26b80408c (ane[0], offset 0x180408c) = 0x2
[cpu2] [0xfffffe001387b1a8] MMIO: W.4   0x26b804090 (ane[0], offset 0x1804090) = 0x2b45c003
[cpu2] [0xfffffe001387b1a8] MMIO: W.4   0x26b804094 (ane[0], offset 0x1804094) = 0x2
[cpu2] [0xfffffe001387b1a8] MMIO: W.4   0x26b804080 (ane[0], offset 0x1804080) = 0x31
[cpu2] [0xfffffe001387b1a8] MMIO: W.4   0x26b8040c4 (ane[0], offset 0x18040c4) = 0x1
[cpu2] [0xfffffe001387b1a8] MMIO: W.4   0x26b8040c8 (ane[0], offset 0x18040c8) = 0x3b70c000
[cpu2] [0xfffffe001387b1a8] MMIO: W.4   0x26b8040cc (ane[0], offset 0x18040cc) = 0x2
[cpu2] [0xfffffe001387b1a8] MMIO: W.4   0x26b8040d0 (ane[0], offset 0x18040d0) = 0x3b70c033
[cpu2] [0xfffffe001387b1a8] MMIO: W.4   0x26b8040d4 (ane[0], offset 0x18040d4) = 0x2
[cpu2] [0xfffffe001387b1a8] MMIO: W.4   0x26b8040c0 (ane[0], offset 0x18040c0) = 0x31
"""


def apply_ane_dart_tunables(ane):
    ane.p.write32(0x26b804004, 0x1)
    ane.p.write32(0x26b804008, 0x824000)
    ane.p.write32(0x26b80400c, 0x8)
    ane.p.write32(0x26b804010, 0x8c7fff)
    ane.p.write32(0x26b804014, 0x8)
    ane.p.write32(0x26b804000, 0x11)
    ane.p.write32(0x26b804044, 0x1)
    ane.p.write32(0x26b804048, 0x0)
    ane.p.write32(0x26b80404c, 0xf)
    ane.p.write32(0x26b804050, 0xffffffff)
    ane.p.write32(0x26b804054, 0xf)
    ane.p.write32(0x26b804040, 0x33)
    ane.p.write32(0x26b804084, 0x1)
    ane.p.write32(0x26b804088, 0x2b45c000)
    ane.p.write32(0x26b80408c, 0x2)
    ane.p.write32(0x26b804090, 0x2b45c003)
    ane.p.write32(0x26b804094, 0x2)
    ane.p.write32(0x26b804080, 0x31)
    ane.p.write32(0x26b8040c4, 0x1)
    ane.p.write32(0x26b8040c8, 0x3b70c000)
    ane.p.write32(0x26b8040cc, 0x2)
    ane.p.write32(0x26b8040d0, 0x3b70c033)
    ane.p.write32(0x26b8040d4, 0x2)
    ane.p.write32(0x26b8040c0, 0x31)
    return

