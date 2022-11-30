# SPDX-License-Identifier: MIT
from ..utils import *
from .dart import DARTRegs

class R_TQINFO(Register32):
    UNK = 31, 16
    NID = 15, 0

class TaskQueue(RegMap):
    STATUS     = irange(0x00, 8, 0x148), Register32
    PRTY       = irange(0x10, 8, 0x148), Register32
    FREE_SPACE = irange(0x14, 8, 0x148), Register32
    TQINFO     = irange(0x1c, 8, 0x148), R_TQINFO

    BAR1 = (irange(0x20, 8, 0x148), irange(0x0, 0x20, 4)), Register32
    REQ_NID1  = irange(0xa0, 8, 0x148), Register32
    REQ_SIZE2 = irange(0xa4, 8, 0x148), Register32
    REQ_ADDR2 = irange(0xa8, 8, 0x148), Register32

    BAR2 = (irange(0xac, 8, 0x148), irange(0x0, 0x20, 4)), Register32
    REQ_NID2  = irange(0x12c, 8, 0x148), Register32
    REQ_SIZE1 = irange(0x130, 8, 0x148), Register32
    REQ_ADDR1 = irange(0x134, 8, 0x148), Register32


class R_REQINFO(Register32): 
    TDSIZE  = 31, 16
    TDCOUNT = 15,  0

class R_IRQINFO(Register32): 
    CNT  = 31, 24
    NID  = 23, 16
    UNK1 = 15, 8
    UNK2 = 7,  0

class TMRegs(RegMap): 
    REQ_ADDR = 0x0, Register32
    REQ_INFO = 0x4, R_REQINFO
    REQ_PUSH = 0x8, Register32
    TQ_EN    = 0xc, Register32

    IRQ_EVT1_CNT      = 0x14, Register32
    IRQ_EVT1_DAT_INFO = 0x18, R_IRQINFO
    IRQ_EVT1_DAT_UNK1 = 0x1c, Register32
    IRQ_EVT1_DAT_TIME = 0x20, Register32
    IRQ_EVT1_DAT_UNK2 = 0x24, Register32

    IRQ_EVT2_CNT      = 0x28, Register32
    IRQ_EVT2_DAT_INFO = 0x2c, R_IRQINFO
    IRQ_EVT2_DAT_UNK1 = 0x30, Register32
    IRQ_EVT2_DAT_TIME = 0x34, Register32
    IRQ_EVT2_DAT_UNK2 = 0x38, Register32

    COMMIT_INFO = 0x44, Register32
    TM_STATUS   = 0x54, Register32

    UNK_IRQ_EN1 = 0x68, Register32
    UNK_IRQ_ACK = 0x6c, Register32
    UNK_IRQ_EN2 = 0x70, Register32


class TD_HDR0(Register32): 
    TID  = 31, 24
    NID  = 23, 16
    LNID = 15, 8
    EON  = 7,  0


class ANEPerfRegs(RegMap): 
    CTRL   = 0x190c000, Register64
    DMA_RW = 0x190c0b8, Register64
    DMA_R  = 0x190c0c0, Register64


class ANERegs(RegMap): 
    PMGR1 = 0x738, Register32
    PMGR2 = 0x798, Register32
    PMGR3 = 0x7f8, Register32

    ASC_IO_RVBAR = 0x1050000, Register32
    ASC_EDPRCR   = 0x1010310, Register32

    # 24hz clocks, counter at +4
    CLK0 = 0x1160008, Register32
    CTR0 = 0x116000c, Register32
    CLK1 = 0x1168008, Register32
    CTR1 = 0x116800c, Register32
    CLK2 = 0x1170000, Register32
    CTR2 = 0x1170004, Register32
    CLK3 = 0x1178000, Register32
    CTR3 = 0x1178004, Register32

    VERSION = 0x1840000, Register32

    # for acks during rtkit fw init/deinit
    GPIO0 = 0x1840048, Register32
    GPIO1 = 0x184004c, Register32
    GPIO2 = 0x1840050, Register32
    GPIO3 = 0x1840054, Register32
    GPIO4 = 0x1840058, Register32
    GPIO5 = 0x184005c, Register32
    GPIO6 = 0x1840060, Register32
    GPIO7 = 0x1840064, Register32


class ANEDARTRegs(DARTRegs): 
    UNK_CONFIG_68 = 0x68, Register32
    UNK_CONFIG_6c = 0x6c, Register32
