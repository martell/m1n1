# SPDX-License-Identifier: MIT


class ANEPSManager:
    def __init__(self, ane):
        self.u = ane.u
        self.p = ane.p

        node_addr = self.u.adt["arm-io/ane"].get_reg(1)[0]
        if (node_addr == 0x23b700000):
            # either h13 or h14 since same mmio rnge
            if (ane.regs.VERSION.val == 0xd204a): # t8103
                self.ps_base_addr = 0x23b70c000
            else:
                self.ps_base_addr = 0x23b70c010
        elif (node_addr == 0x28e080000): # ane0
            self.ps_base_addr = 0x28e08c000
        elif (node_addr == 0x28e680100): # ane1
            self.ps_base_addr = 0x28e684000
        elif (node_addr == 0x228e080000): # ane2
            self.ps_base_addr = 0x228e08c000
        elif (node_addr == 0x228e680100): # ane3
            self.ps_base_addr = 0x228e684000
        else:
            raise ValueError("invalid node addr")

        self.ps_regs = [self.ps_base_addr + offset
                        for offset in range(0x0, 0x38, 0x8)]
        return
    
    def powerdown_pds(self):
        # last->first
        for ps_reg in self.ps_regs[::-1]:
            self.p.write32(ps_reg, 0x300)
        return

    def powerup_pds(self):
        # first->last
        for ps_reg in self.ps_regs:
            self.p.write32(ps_reg, 0xf)
        return

    def pd_is_on(self, pd_value):
        return ((pd_value & 0xff) == 0xff)

    def read_pds(self):
        for pd_id, ps_reg in enumerate(self.ps_regs):
            pd_value = self.p.read32(ps_reg)
            print('pd %d: 0x%x, is_on: %r'
                  % (pd_id, pd_value, self.pd_is_on(pd_value)))
        return

    def assert_pds_on(self):
        for pd_id, ps_reg in enumerate(self.ps_regs):
            pd_value = self.p.read32(ps_reg)
            if not (self.pd_is_on(pd_value)):
                raise ValueError('pd %d @ 0x%x is 0x%x'
                                 % (pd_id, ps_reg, pd_value))
        return


def powerup(ane):
    print('powering up ane...')

    ane.apply_static_tunables()
    apply_more_pmgr_tunables(ane)

    # something perf
    ane.p.write32(0x26b908000, 0x0)
    ane.p.write32(0x26b908000, 0x1)

    # ---- ps ----
    ane.psmngr.powerdown_pds()
    unk_power_sequence(ane)
    ane.apply_static_tunables()
    ane.psmngr.powerup_pds()
    ane.psmngr.read_pds()
    ane.psmngr.assert_pds_on()

    # ---- ps ----
    ane.perf_regs.CTRL.val = 0xfff00000fff  # on
    ane.apply_static_tunables()
    pwr_reset_at_init(ane)
    ane.apply_static_tunables()
    ane.perf_regs.CTRL.val = 0xfff00000fff  # reset turns it off
    print('ane powered up!')
    return


def powerdown(ane):
    print('powering down ane...')
    ane.perf_regs.CTRL.val = 0xfff # off
    ane.psmngr.powerdown_pds()
    ane.psmngr.read_pds()
    unk_power_sequence(ane)
    return


def pwr_reset_at_init(ane):
    ane.regs.ASC_EDPRCR.val = 0x2
    ane.regs.PMGR1.val = 0xffff  # re-apply tunables !!!
    ane.regs.PMGR2.val = 0xffff
    ane.regs.PMGR3.val = 0xffff
    # unk asc reset; stuff breaks otherwise
    ane.p.write32(ane.base_addr + 0x1400900, 0xffffffff)
    ane.p.write32(ane.base_addr + 0x1400904, 0xffffffff)
    ane.p.write32(ane.base_addr + 0x1400908, 0xffffffff)
    return


def apply_more_pmgr_tunables(ane):
    p = ane.p
    p.write32(0x26a008000, 0x9)
    p.read32(0x26a000920)
    p.write32(0x26a000920, 0x80)
    p.write32(0x26a008008, 0x7)
    p.write32(0x26a008014, 0x1)
    p.read32(0x26a008018)
    p.write32(0x26a008018, 0x1)
    p.read32(0x26a000748)
    p.write32(0x26a000748, 0x1)
    p.write32(0x26a008208, 0x2)
    p.write32(0x26a008280, 0x20)
    p.write32(0x26a008288, 0x3)
    p.write32(0x26a00828c, 0xc)
    p.write32(0x26a008290, 0x18)
    p.write32(0x26a008294, 0x30)
    p.write32(0x26a008298, 0x78)
    p.write32(0x26a00829c, 0xff)
    p.read32(0x26a0082b8)
    p.write32(0x26a0082b8, 0x1)
    p.write32(0x26a0082bc, 0x1)
    p.read32(0x26a0082c0)
    p.write32(0x26a0082c0, 0x1)
    p.read32(0x26a000748)
    p.write32(0x26a000748, 0x1)
    p.write32(0x26a00820c, 0x3)
    p.write32(0x26a008284, 0x20)
    p.write32(0x26a0082a0, 0x3)
    p.write32(0x26a0082a4, 0xc)
    p.write32(0x26a0082a8, 0x18)
    p.write32(0x26a0082ac, 0x30)
    p.write32(0x26a0082b0, 0x78)
    p.write32(0x26a0082b4, 0xff)
    p.read32(0x26a0082b8)
    p.write32(0x26a0082b8, 0x3)
    p.write32(0x26a0082bc, 0x2)
    p.read32(0x26a0082c0)
    p.write32(0x26a0082c0, 0x3)
    p.write32(0x26a008210, 0x0)
    p.write32(0x26a008408, 0xd)
    p.write32(0x26a008418, 0x3)
    p.write32(0x26a00841c, 0x0)
    p.write32(0x26a008420, 0xffffffff)
    p.write32(0x26a008424, 0x0)
    p.write32(0x26a008428, 0xfff)
    p.read32(0x26a0082b8)
    p.write32(0x26a0082b8, 0x7)
    p.write32(0x26a0082bc, 0x4)
    p.read32(0x26a0082c0)
    p.write32(0x26a0082c0, 0x7)
    return

def unk_power_sequence(ane):
    p = ane.p
    p.read64(0x26a00c000)
    p.write32(0x26a008014, 0x1)
    p.read64(0x26a00c200)
    p.read64(0x26a00c230)
    p.read64(0x26a00c260)
    p.read64(0x26a00c290)
    p.read64(0x26a00c298)
    p.read64(0x26a00c2a0)
    p.read64(0x26a00c2a8)
    p.read64(0x26a00c2b0)
    p.read64(0x26a00c2b8)
    p.write32(0x26a0082bc, 0x1)
    p.read64(0x26a00c208)
    p.read64(0x26a00c238)
    p.read64(0x26a00c268)
    p.read64(0x26a00c2c0)
    p.read64(0x26a00c2c8)
    p.read64(0x26a00c2d0)
    p.read64(0x26a00c2d8)
    p.read64(0x26a00c2e0)
    p.read64(0x26a00c2e8)
    p.write32(0x26a0082bc, 0x2)
    p.read64(0x26a00c270)
    p.write32(0x26a0082bc, 0x4)
    return
