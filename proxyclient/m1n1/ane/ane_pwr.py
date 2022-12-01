# SPDX-License-Identifier: MIT


class ANEPSManager:
    def __init__(self, ane):
        self.u = ane.u
        self.p = ane.p
        self.ps_base_addr = self.u.adt["arm-io/ane"].get_reg(1)[0]
        self.ps_regs = [self.ps_base_addr + offset
                        for offset in range(0xc000, 0xc038, 0x8)]
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
    # something perf
    ane.p.write32(0x26b908000, 0x0)
    ane.p.write32(0x26b908000, 0x1)

    ane.psmngr.powerdown_pds()
    ane.psmngr.powerup_pds()
    ane.psmngr.read_pds()
    ane.psmngr.assert_pds_on()

    ane.perf_regs.CTRL.val = 0xfff00000fff  # on
    print('ane powered up!')
    return

def powerdown(ane):
    print('powering down ane...')
    ane.perf_regs.CTRL.val = 0xfff # off
    ane.psmngr.powerdown_pds()
    ane.psmngr.read_pds()
    unk_power_sequence(ane)
    return
