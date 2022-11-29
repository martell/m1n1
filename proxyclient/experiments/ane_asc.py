
#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from m1n1.setup import *

import os
import json
import time
import struct
from construct import *

from m1n1.hw.dart import DART
from m1n1.proxyutils import RegMonitor
from m1n1.shell import run_shell

from ane.ane_boot import ane_boot
from ane.ane_utils import parse_ane_segment_ranges
from ane.ane_utils import zero_pad, ez_unpack, ez_pack
from ane.ane_constants import *

#--------------------------------------------------------------
# config
FW_ACK_MAX_TRIES = 15
DBG_REGMON_ON = 1

#--------------------------------------------------------------
# pre init
node = u.adt["/arm-io/ane"]
ane_base = u.adt["arm-io/ane"].get_reg(0)[0] # 0x26a000000
pwr_base = u.adt["arm-io/ane"].get_reg(1)[0] # 0x23b700000

# regs
# used for init/deinit communication
ANE_GPIO0 = ane_base + 0x1840048
ANE_GPIO1 = ane_base + 0x184004c
ANE_GPIO2 = ane_base + 0x1840050
ANE_GPIO3 = ane_base + 0x1840054
ANE_GPIO4 = ane_base + 0x1840058
ANE_GPIO5 = ane_base + 0x184005c
ANE_GPIO6 = ane_base + 0x1840060
ANE_GPIO7 = ane_base + 0x1840064
ANE_GPIO_ALL = (ANE_GPIO0, ANE_GPIO1, ANE_GPIO2, ANE_GPIO3,
                ANE_GPIO4, ANE_GPIO5, ANE_GPIO6, ANE_GPIO7)

# 24hz clocks, counter at +4
ANE_CLOCK0 = ane_base + 0x1160008
ANE_CLOCK1 = ane_base + 0x1168008
ANE_CLOCK2 = ane_base + 0x1170000 # macos only uses this one tho
ANE_CLOCK3 = ane_base + 0x1178000
ANE_CLOCK_ALL = (ANE_CLOCK0, ANE_CLOCK1, ANE_CLOCK2, ANE_CLOCK3)

ANE_PMGR_CNTRL0 = ane_base + 0x738
ANE_PMGR_CNTRL2 = ane_base + 0x798
ANE_PMGR_CNTRL2 = ane_base + 0x7f8

ANE_CPU_EDPRCR = ane_base + 0x1010310 # ANE_H11_ASC_CPU_EDPRCR

# --------------------------------------------------------------

# let's a go!

p.pmgr_adt_clocks_enable(f'/arm-io/ane')
p.pmgr_adt_clocks_enable(f'/arm-io/dart-ane')

dart = DART.from_adt(u, path="/arm-io/dart-ane")
dart.initialize()

ttbr_base_phy = ane_boot(dart)
dart.regs.dump_regs()
print('\n'*2)

# --------------------------------------------------------------

"""
[vmem map]
0x0000000 - 0x00a4000 (size 0xa4000): ctrr; fw text section; phys mapped by iboot
0x00a4000 - 0x04dc000 (size 0x438000): ctrr; fw data section; phys mapped by iboot
0x04dc000 - 0x0700000 (size 0x224000): ctrr; heap padded to fw main memory size
0x0704000 - 0x0744000 (size 0x40000): shared; ipc communication
0x0748000 - 0x1f48000 (size 0x1800000): shared; extra heap requested by fw
"""


def parse_ane_segment_ranges(node):
    if ((isinstance(node, str)) and (len(node) == 0x80)):
        # segment_str = "00408200080000000000000000000000004082000800000000400a000300000000403d010800000000400a000000000000400a000f0000000080430000000000"
        unpacked = [struct.unpack('<Q', unhexlify(seg))[0] for seg in chunks(node, size=0x10)]
    else:
        ranges = getattr(node, 'segment-ranges') # an entire c struct lol
        unpacked = struct.unpack('<'+'Q'*(len(ranges)//8), ranges)
        # names = getattr(node, 'segment-names') # "__TEXT;__DATA"
        # names = names.split(';')
    assert(len(unpacked) == 8)
    text, data = list(unpacked[:4]), list(unpacked[4:])
    text[-1] = text[-1] & 0xffffffff # for size
    data[-1] = data[-1] & 0xffffffff
    return text, data
    

def load_ane_fw():
    # H11ANEIn::mapFwCTRRRegion() :H11ANEIn: FW __TEXT segment phy: 0x800824000, virt: 0x0, remap: 0x800824000, size: 0xa4000
    # H11ANEIn::mapFwCTRRRegion() :H11ANEIn: FW __DATA segment phy: 0x8013d4000, virt: 0xa4000, remap: 0xf000a4000, size: 0x438000

    text, data = parse_ane_segment_ranges(node)
    text_phy, text_vir, text_remap, text_size = text
    data_phy, data_vir, data_remap, data_size = data
    print('fw text segment - phy: 0x%x vir: 0x%x remap: 0x%x size: 0x%x' % (text_phy, text_vir, text_remap, text_size))
    print('fw data segment - phy: 0x%x vir: 0x%x remap: 0x%x size: 0x%x' % (data_phy, data_vir, data_remap, data_size))
    dart.iomap_at(0, text_vir, text_phy, text_size)
    dart.iomap_at(0, data_vir, data_phy, data_size)
    return data_vir, data_size


def load_ane_fw_heap_dart(data_vir, data_size):
    # H11ANEIn::AllocateHeapMemorySurface: physical start: 0x4dc000, heap size: 0x224000
    # H11ANEIn::start(IOService *) :H11ANEIn: CTRR firmware is loaded, size: 0x700000

    heap_vir = data_vir + data_size # 0x4dc000
    heap_size = CTRR_FW_SIZE - heap_vir # 0x224000
    heap_phy = u.heap.memalign(PAGE_SIZE, heap_size)
    p.memset32(heap_phy, 0, heap_size)

    print('heap_phy: 0x%x' % (heap_phy))
    dart.iomap_at(0, heap_vir, heap_phy, heap_size)

    print('ctrr fw loaded')
    return

data_vir, data_size = load_ane_fw()
dart.regs.dump_regs()

load_ane_fw_heap_dart(data_vir, data_size)

#--------------------------------------------------------------

if DBG_REGMON_ON:
    rnges = [
            (0x26a000000, 0x26a001000),
            (0x26b000000, 0x26b010020),
            (0x26b050000, 0x26b0ffff0),

            (0x26b100000, 0x26b1ffffc),
            (0x26b400000, 0x26b457100),

            (0x26b800000, 0x26b808000),
            (0x26b840000, 0x26b854000),

            (0x26b860000, 0x26b86fffc),
            (0x26b874000, 0x26b875000),

            (0x26b900000, 0x26b90c000),
            (0x26b90c000, 0x26b90c1fc),

            (0x26bc04000, 0x26bc06000),
            (0x26bc06000, 0x26bc087fc),
            (0x26bc09014, 0x26bc09ffc),
            (0x26bc10000, 0x26bc107fc),
            (0x26bc11000, 0x26bc28000),
            ]

    mon = RegMonitor(u)

    for (start, end) in rnges:
        mon.add(start, end-start)

    mon.poll() # should work after ane_boot

#--------------------------------------------------------------
# checks to make sure ane is powered on

# assert clocks are running
for clock_addr in ANE_CLOCK_ALL:
    prev = p.read32(clock_addr)
    curr = p.read32(clock_addr)
    print("prev: 0x%x curr: 0x%x diff: 0x%x" % (prev, curr, curr-prev))
    assert(curr > prev)

#--------------------------------------------------------------

def power_gating_disabled_reset():
    p.write32(ane_base + 0x1010310, 0x2) # ANE_H11_ASC_CPU_EDPRCR

    p.write32(ane_base + 0x738, 0xffff)
    p.write32(ane_base + 0x798, 0xffff)
    p.write32(ane_base + 0x7f8, 0xffff)

    p.write32(ane_base + 0x1400900, 0xffffffff)
    p.write32(ane_base + 0x1400904, 0xffffffff)
    p.write32(ane_base + 0x1400908, 0xffffffff)
    return

power_gating_disabled_reset()
time.sleep(0.5)

#--------------------------------------------------------------
# status inits at 0x28;
# becomes -> 0x2e after fw mapping

def get_asc_status():
    # status is given in 0x2X fmt
    status = p.read32(ane_base + 0x1400048) # ASCWRAP_IDLE_STATUS
    print("asc status: 0x%x" % status)
    if (status & 3) == 0:
        # can't be 0x28, 0x2c
        print("ANECPU not in WFI")
        return 0
    print("ANECPU in WFI")
    return 1

for n in range(15):
    if (get_asc_status()):
        break
    time.sleep(0.1)

# it should be wfi for now
assert(get_asc_status())

#--------------------------------------------------------------

# so we can init it using chinook sequence below
def chinook_seq():
    p.read32(ANE_GPIO1) # necessary?

    for gpio_reg in ANE_GPIO_ALL:
        p.write32(gpio_reg, 0x0)

    p.write32(ane_base + 0x1400044, 0x0) # cpu control
    p.write32(ane_base + 0x1400044, 0x10)

    p.write32(ANE_GPIO7, 0x0) # init call
    return

print('starting chinook bootup sequence...')
chinook_seq()

#--------------------------------------------------------------

time.sleep(1)

# do NOT touch other regs here
# not even reads; so no mon.poll()
# ESPECIALLY asc region
# else it wont boot


def apply_ane_pmgr_tunables_2_v2():
    # absolutely fucking necessary
    # will NOT boot otherwise

    pmgr_tunables_mapper = [(0x0, 0x10), (0x38, 0x50020), (0x3c, 0xa0030),
                            (0x400, 0x40010001), (0x600, 0x1ffffff),
                            (0x738, 0x200020), (0x798, 0x100030), (0x7f8, 0x100000a),
                            (0x900, 0x101),
                            (0x410, 0x1100), (0x420, 0x1100), (0x430, 0x1100)]
    for (offset, new) in pmgr_tunables_mapper:
        addr = ane_base + offset
        curr = p.read32(addr)
        p.write32(addr, new)
    return

print('applying tunables...')
# apply_gen_ane_tunables()

apply_ane_pmgr_tunables_2_v2()

#--------------------------------------------------------------

perf_regs = [0x26b90c080, 0x26b90c088, 0x26b90c090, 0x26b90c098,
                0x26b90c0a0, 0x26b90c0a8, 0x26b90c0b0, 0x26b90c0b8, 0x26b90c0c0]
for reg in perf_regs:
    val = p.read64(reg)
p.write64(0x26b90c000, 0xfff00000fff) # perf controller init

#--------------------------------------------------------------

for n in range(FW_ACK_MAX_TRIES):
    val = p.read32(ANE_GPIO7)
    print('val is: 0x%x' % val)
    if (val == ANE_ACK_MAGIC1):
        break
    time.sleep(0.1)

# "ANE%d: %s :H11ANEIn::ANE_Init - No wake signal from second rANE_SCRATCH7 ANECPU\n"
assert((p.read32(ANE_GPIO7) == ANE_ACK_MAGIC1))
print('got fw ack at GPIO7 using ANE_ACK_MAGIC1 (0x%x)' % ANE_ACK_MAGIC1)

# now fw hangs until magic2 in gpio7

# again, do NOT touch regs here;
# else fw communication sequence gets messed up

# print("H11ANE::ANE_Init ANE wakeup from sleep completed in %lld uS, res=0x%x\n")
print('reading fw requested resources in GPIOs...')

IPC_CHAN_COUNT = p.read32(ANE_GPIO0) # 0x7
IPC_QUEUE_SIZE = p.read32(ANE_GPIO1) # 0xf340
# this always gives 0x100; likely IPC_CHAN_TABLE_WIDTH
# but since i hard-code chan entry structs anyway
# don't think there's meaning in using
unk_100 = p.read32(ANE_GPIO2)
FW_HEAP_SIZE = p.read32(ANE_GPIO3) # 0x1800000

print('ANE_GPIO0: IPC_CHAN_COUNT: %d' % IPC_CHAN_COUNT)
print('ANE_GPIO1: IPC_QUEUE_SIZE: 0x%x' % IPC_QUEUE_SIZE)
print('ANE_GPIO3: fw requested extra heap size: 0x%x' % FW_HEAP_SIZE)

#--------------------------------------------------------------
# ipc stuff

IPCMsg = Struct(
    "pad" / Default(Int32ul, 0),
    "pad" / Default(Int32ul, 0),
    "ipc_base" / Hex(Int64ul),
    "ctrr_size" / Int64ul,
    "ctrr_size2" / Int64ul,
    "shared_base" / Int64ul,
    "shared_size" / Int64ul,
    "pad" / Default(Int32ul, 0),
    "pad" / Default(Int32ul, 0),
    "pad" / Default(Int32ul, 0),
    "pad" / Default(Int32ul, 0),
    "pad" / Default(Int32ul, 0),
    "pad" / Default(Int32ul, 0),
    "pad" / Default(Int32ul, 0),
    "pad" / Default(Int32ul, 0),
    "ipc_size" / Int64ul,
    "pad" / Default(Int32ul, 0),
    "pad" / Default(Int32ul, 0),
    "pad" / Default(Int32ul, 0),
    "pad" / Default(Int32ul, 0),
    "unk0" / Int32ul,
    "unk1" / Int32ul,
)

assert(IPCMsg.sizeof() == IPC_MSG_SIZE)


IPCChanTableEntry = Struct(
    "name" / PaddedString(0x40, "utf8"),
    "type" / Int32ul,
    "idx" / Int32ul,
    "size" / Int32ul,
    "pad" / Int32ul,
    "vaddr" / Hex(Int32ul),
    "pad" / Default(Int32ul, 0),
    "pad" / Default(Int32ul, 0),
    "pad" / Default(Int32ul, 0),
)


def prep_ipc(ipc_msg_offset):
    # prep shared ipc buf
    ipc_phys = u.heap.memalign(PAGE_SIZE, IPC_BUF_SIZE)
    p.memset32(ipc_phys, 0, IPC_BUF_SIZE)

    print('ipc_phys: 0x%x ipc_vir: 0x%x ipc_size: 0x%x' % (ipc_phys, IPC_WIRED_BASE, IPC_BUF_SIZE))
    dart.iomap_at(0, IPC_WIRED_BASE, ipc_phys, IPC_BUF_SIZE)

    # prep ipc msg
    """
    00003380: 00000000 00000000 00704000 00000000  .........@p.....
    00003390: 00700000 00000000 0f900000 00000000  ..p.............
    000033a0: 00748000 00000000 01800000 00000000  ..t.............
    000033d0: 00040000 00000000 00000000 00000000  ................
    000033e0: 00000000 00000000 00000040 00000004  ........@.......
    """
    ipc_msg_buf = IPCMsg.build(dict(
                        ipc_base=IPC_WIRED_BASE,
                        ctrr_size=CTRR_FW_SIZE, ctrr_size2=0x10000000-CTRR_FW_SIZE,
                        shared_base=SHARED_HEAP_BASE, shared_size=SHARED_HEAP_SIZE,
                        ipc_size=IPC_BUF_SIZE, unk0=0x40, unk1=0x0))
    dart.iowrite(0, IPC_WIRED_BASE + ipc_msg_offset, ipc_msg_buf)
    return

#--------------------------------------------------------------

# heap allocation
"""
H11ANEIn::ANE_Init() :H11ANEIn::ANE_Init - Requested firmware heap size=25165824 // 0x1800000
H11ANEIn::AllocateSharedMemorySurface: Shared memory region mapped at DART translated address: 0x0000000000748000, requireMap: 0
H11ANEIn::AllocateSharedMemorySurface - Successfully allocated surface. surface-id=0x00000018, size=0x1800000, dartMapBase=0x748000
"""

def fw_requested_heap_alloc():
    shared_heap_phys = u.heap.memalign(PAGE_SIZE, FW_HEAP_SIZE)
    p.memset32(shared_heap_phys, 0, FW_HEAP_SIZE)
    dart.iomap_at(0, SHARED_HEAP_BASE, shared_heap_phys, FW_HEAP_SIZE)
    return 0

#--------------------------------------------------------------

def read_vmem():
    headdir = "vmem/"
    os.makedirs(headdir, exist_ok=True)

    size = 0x4000
    rnges = [('text', 0, 0x00a4000), ('data', 0x00a4000, 0x04dc000),
             ('heap', 0x04dc000, 0x0700000), ('ipc', 0x0704000, 0x0744000)]
    for (name, start, end) in rnges:
        dirname = name
        outdir = os.path.join(headdir, dirname)
        os.makedirs(outdir, exist_ok=True)

        for vaddr in range(start, end, size):
            outfile = os.path.join(outdir, "0x%x.bin" % vaddr)
            # print("dumping 0x%x..." % vaddr)
            try:
                data = dart.ioread(0, vaddr, size)
            except:
                # print("Exception: Unmapped page at iova 0x%x" % vaddr)
                continue
            open(outfile, "wb").write(data)

    return 0

#--------------------------------------------------------------

def init_stage_2():

    fw_requested_heap_alloc()

    # ipc init
    ipc_msg_offset = 0xf380 # idk its what macos uses
    prep_ipc(ipc_msg_offset)

    p.write32(ANE_GPIO0, IPC_WIRED_BASE + ipc_msg_offset) # 0x713380
    p.write32(ANE_GPIO1, 0x0)

    time.sleep(5)
    p.write32(ANE_GPIO7, ANE_ACK_MAGIC2) # signal to fw

    if 1:
        for n in range(FW_ACK_MAX_TRIES):
            val = p.read32(ANE_GPIO7)
            print('ANE_GPIO7: 0x%x' % val)
            if (val == ANE_ACK_MAGIC1):
                break
            time.sleep(0.05)

    print('ANE_GPIO7 is 0x%x' % (p.read32(ANE_GPIO7)))

    ipc_init_stage = p.read32(ANE_GPIO6)
    print('ipc init sequence is at stage %d' % ipc_init_stage)
    if (ipc_init_stage == 0):
        print('init stage 2 failed desperately')
        return -1

    if DBG_REGMON_ON:
        mon.poll() # refresh?

    read_vmem()

    if (0 == 1) and (ipc_init_stage >= 7):
        print('ipc chan table available. reading chan table...')
        chan_table_data = dart.ioread(0, IPC_WIRED_BASE, IPC_CHAN_COUNT*IPC_CHAN_TABLE_WIDTH)
        for n in range(IPC_CHAN_COUNT):
            entry = chan_table_data[n*IPC_CHAN_TABLE_WIDTH:(n*IPC_CHAN_TABLE_WIDTH)+IPC_CHAN_TABLE_WIDTH]
            x = IPCChanTableEntry.parse(entry)
            print(x)

    # = "ANE%d: %s :H11ANEIn::ANE_Init - No second int from ANECPU..Retrying power up, retries=%d\n"
    # = "ANE#%d:%s :H11ANEIn::ANE_Init - Got second int from ANECPU (channel description table ready)\n"
    # H11ANEIn::ANE_Init - Found channel 6 in the channel table. Type=1 (IO_T2H), Source=6, size: 16
    # ANECPU Ready. About to enable ANE interrupts
    return


init_stage_2()

#--------------------------------------------------------------




run_shell(globals(), msg="Have fun!")


