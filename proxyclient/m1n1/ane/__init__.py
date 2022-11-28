# SPDX-License-Identifier: MIT

import time
import struct

from m1n1.hw.dart import DART
from m1n1.hw.ane import ANERegs, ANEPerfRegs

from m1n1.ane.ane_pwr import powerup
from m1n1.ane.ane_dart import init_ane_dart_regs
from m1n1.ane.ane_context import ANEBufManager
from m1n1.ane.ane_tiler import ANETiler


class ANE:

    PAGE_SIZE = 0x4000
    TILE_SIZE = 0x4000

    def __init__(self, u):
        self.start_time = time.time()

        self.u = u
        self.p = u.proxy
        self.iface = u.iface

        self.p.pmgr_adt_clocks_enable(f'/arm-io/ane')
        self.p.pmgr_adt_clocks_enable(f'/arm-io/dart-ane')
        self.base_addr = u.adt["arm-io/ane"].get_reg(0)[0]
        self.apply_static_pmgr_tunables()

        # "No ane-type in device tree, fall back to
        # determine device type by reading registers"
        assert (self.p.read32(0x26b840000) == 0xd204a)  # t8103
        self.regs = ANERegs(self.u, self.base_addr)
        self.perf_regs = ANEPerfRegs(self.u, self.base_addr)

        self.dart = DART.from_adt(u, path="/arm-io/dart-ane", instance=0)
        self.dart.initialize()
        self.dart_regs_all = init_ane_dart_regs(self)

        self.bufmngr = ANEBufManager(self)
        self.tiler = ANETiler()  # static
        return

    def apply_static_tunables(self):
        # this cost me a solid week
        static_tunables_map = [
            (0x0, 0x10), (0x38, 0x50020), (0x3c, 0xa0030),
            (0x400, 0x40010001), (0x600, 0x1ffffff),
            (0x738, 0x200020), (0x798, 0x100030),
            (0x7f8, 0x100000a), (0x900, 0x101), (0x410, 0x1100),
            (0x420, 0x1100), (0x430, 0x1100)]
        for (offset, value) in static_tunables_map:
            self.p.write32(self.base_addr + offset, value)
        return

    def powerup(self):
        """
        ane.powerup() ensures a bare "playground"
        i.e. regs accessible, asc in WFI, perf running
        """
        powerup(self)
        return

    def get_timestamp(self):
        # unk why there are 4 clocks
        # macos only uses CLK2 for irqs so
        timestamp = self.regs.CLK2.val
        counter = self.regs.CTR2.val
        print('current timestamp: 0x%x, counter: %d' % (timestamp, counter))
        return (timestamp, counter)

    def ioread(self, iova, size):
        return self.dart.ioread(0, iova & 0xFFFFFFFF, size)

    def iowrite(self, iova, buf):
        self.dart.iowrite(0, iova & 0xFFFFFFFF, buf)
        return

    def syncttbr(self):
        """
        since ttbr inits after first alloc
        call to sync the other 2 instances
        """
        ttbr0_addr = self.dart.regs.TTBR[0, 0].val
        print('updated ttbr0_addr: 0x%x' % ttbr0_addr)
        self.dart_regs_all[1].TTBR[0, 0].val = ttbr0_addr
        self.dart_regs_all[2].TTBR[0, 0].val = ttbr0_addr
        for instance in range(3):
            assert (self.dart_regs_all[instance].TTBR[0, 0].val == ttbr0_addr)
        return ttbr0_addr

    def get_dma_perf_stats(self):
        dma_rw = self.perf_regs.DMA_RW.val
        dma_r = self.perf_regs.DMA_R.val
        dma_w = dma_rw - dma_r
        return (dma_r, dma_w, dma_rw)
