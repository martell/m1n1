# SPDX-License-Identifier: MIT

class Task:
    def __init__(self, req_iova=None, nid=None, bar=None, size=None):
        self.req_iova = req_iova
        self.nid = nid
        self.bar = bar
        self.size = size
        return

    def setup_BAR(self, bardict):
        self.bar = BAR()
        for key in bardict:
            setattr(self.bar, key, bardict[key])
        return

class BAR:
    def __init__(self):
        self.p_head = 0
        self.p_krn = 0
        self.p_2 = 0
        self.p_3 = 0
        self.p_dst = 0
        self.p_src1 = 0
        self.p_src2 = 0
        self.p_7 = 0
        self.p_8 = 0
        self.p_9 = 0
        self.p_a = 0
        self.p_b = 0
        self.p_c = 0
        self.p_d = 0
        self.p_e = 0
        self.p_f = 0
        self.p_10 = 0
        self.p_11 = 0
        self.p_12 = 0
        self.p_13 = 0
        self.p_14 = 0
        self.p_15 = 0
        self.p_16 = 0
        self.p_17 = 0
        self.p_18 = 0
        self.p_19 = 0
        self.p_1a = 0
        self.p_1b = 0
        self.p_1c = 0
        self.p_1d = 0
        self.p_1e = 0
        self.p_1f = 0
        return

    def get_table(self):
        return list(vars(self).values())
