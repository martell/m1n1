# SPDX-License-Identifier: MIT

import time
from m1n1.hw.ane import TMRegs, TaskQueue


class TaskManager:
    
    TQ_HW_COUNT = 8
    TQ_WIDTH = 0x148
    tq_prty = (0x1, 0x2, 0x3, 0x4, 0x5, 0x6, 0x1e, 0x1f)

    def __init__(self, ane, base_addr):
        self.u = ane.u
        self.p = ane.p

        self.TM_BASE_ADDR = base_addr + 0x24000 
        self.TQ_BASE_ADDR = base_addr + 0x25000
        
        self.regs = TMRegs(self.u, self.TM_BASE_ADDR)
        self.tq = TaskQueue(self.u, self.TQ_BASE_ADDR)
        return

    def init_tqs(self):
        self.regs.TQ_EN.val = 0x3000

        # set priority param for each queue
        for queue_id, prty in enumerate(self.tq_prty):
            self.tq.PRTY[queue_id].val = self.tq_prty[queue_id]
        
        self.regs.UNK_IRQ_EN1.val = 0x4000000 # messes irq 
        self.regs.UNK_IRQ_EN2.val = 0x6 # messes irq 
        self.p.write32(0x26b874008, 0x3) # optional asc signal
        return

    def enqueue_tq(self, task, queue_id=4):
        if not ((queue_id >= 0) and (queue_id < self.TQ_HW_COUNT)):
            raise ValueError('8 hw queues available; 0 <= queue_id <= 7')
        
        if not (self.tq.PRTY[queue_id].val == self.tq_prty[queue_id]):
            raise ValueError('invalid priority param setup for tq %d' % queue_id)
        
        print('enqueueing task w/ nid 0x%x @ 0x%x to tq %d' 
                                            % (task.nid, task.req_iova, queue_id))
        self.tq.STATUS[queue_id].val = 0x1

        for bar_idx, bar_val in enumerate(task.bar.get_table()):
            self.tq.BAR1[queue_id, bar_idx].val = bar_val

        # req transformations derived from task
        req_size = task.size * 0x4000 + 0x1ff0000 & 0x1ff0000
        # if | 1 is gone, it doesn't go through !!!
        req_nid = (task.nid & 0xff) << 8 | 1  # 0x2d -> 0x2d01
        self.tq.REQ_SIZE1[queue_id].val = req_size # nxt
        self.tq.REQ_ADDR1[queue_id].val = task.req_iova
        self.tq.REQ_NID1[queue_id].val = req_nid # INVERTED

        self.tq.REQ_SIZE2[queue_id].val = 0x0 # clear other req size
        self.tq.REQ_ADDR2[queue_id].val = 0x0 # clear other req 
        return

    def arbitrate_tq(self):
        enqueued_tqs = []
        for queue_id, prty in enumerate(self.tq_prty):
            in_use = self.tq.STATUS[queue_id].val == 1 
            if (in_use):
                enqueued_tqs.append(queue_id)
        
        print('task arbiter found %d tq(s) enqueued' % len(enqueued_tqs))
        if (len(enqueued_tqs) == 0):
            print('no tq(s) enqueued; task arbiter failed')
            return -1
        
        return enqueued_tqs[0] # priorities are ordered

    def execute_tq(self):
        arbitered = self.arbitrate_tq()
        if (arbitered <= 0):
            print('execute_tq failed; nothing arbitered')
            return
        queue_id = arbitered
        print('arbitered tq %d; pushing to execution queue...' % queue_id)

        # cp to main queue in (TM rnge)
        self.regs.REQ_ADDR.val = self.tq.REQ_ADDR1[queue_id].val

        # if (num == 0) req doesnt go through
        num_bufs = 1 # TODO derive from BAR
        self.regs.REQ_INFO.val = self.tq.REQ_SIZE1[queue_id].val | num_bufs

        # this write actually triggers the circuit
        # so main queue can be adjusted before this
        # e.g. 3 -> 0x304, 4 -> 0x405
        self.regs.REQ_TRIGGER.val = self.tq_prty[queue_id] | (queue_id & 7) << 8

        assert(self.get_tm_status() == True) 
        self.get_committed_info()
        self.handle_irq()
        self.tq.STATUS[queue_id].val = 0x0 # done
        return
    
    def get_tm_status(self, max_timeouts=10, sleep_int=0.01):
        for n in range(max_timeouts):
            status = self.regs.TM_STATUS.val
            success = (status & 1) != 0
            print('tm status: 0x%x, success: %r' % (status, success))
            if (success): return success
            time.sleep(sleep_int)
        print('timeout, tm is non-idle! status: 0x%x' % status)
        return success

    def get_committed_info(self):
        committed_nid = self.regs.COMMIT_INFO.val >> 0x10 & 0xff
        print('pushed td w/ nid 0x%x to execution' % committed_nid)
        return

    def handle_irq(self):
        evtcnt = self.regs.IRQ_EVT1_CNT.val
        if (evtcnt == 0): return
        
        line = 0
        print('irq handler: LINE %d EVTCNT: %d' % (line, evtcnt))
        for evt_n in range(evtcnt):
            # these have to be cleared
            info = self.regs.IRQ_EVT1_DAT_INFO.val
            unk1 = self.regs.IRQ_EVT1_DAT_UNK1.val 
            timestamp = self.regs.IRQ_EVT1_DAT_TIME.val
            unk2 = self.regs.IRQ_EVT1_DAT_UNK2.val
            print('irq handler: LINE %d EVT %d: executed info 0x%x @ 0x%x' 
                                            % (line, evt_n, info, timestamp))

        # sometimes | 2, sometimes | 4
        self.regs.UNK_IRQ_ACK.val = self.regs.UNK_IRQ_ACK.val | 4

        line = 1
        evtcnt = self.regs.IRQ_EVT2_CNT.val
        print('irq handler: LINE %d EVTCNT: %d' % (line, evtcnt))
        for evt_n in range(evtcnt):
            # these have to be cleared
            info = self.regs.IRQ_EVT2_DAT_INFO.val
            unk1 = self.regs.IRQ_EVT2_DAT_UNK1.val
            timestamp = self.regs.IRQ_EVT2_DAT_TIME.val
            unk2 = self.regs.IRQ_EVT2_DAT_UNK2.val
            print('irq handler: LINE %d EVT %d: executed info 0x%x @ 0x%x' 
                                            % (line, evt_n, info, timestamp))

        return 
