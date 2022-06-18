# SPDX-License-Identifier: MIT
from ..utils import chexdump
from ..malloc import Heap
from construct.core import *
from ..fw.agx.channels import *
from ..fw.agx.cmdqueue import *
from ..fw.agx.microsequence import *
from ..hw.uat import MemoryAttr
from .object import *
import textwrap

class GPUContext:
    def __init__(self, agx):
        self.agx = agx
        self.uat = self.agx.uat
        self.u = self.agx.u
        self.p = self.agx.p
        self.verbose = False

        self.context_info = agx.kshared.new(ContextInfo)
        self.context_info.fb_ptr = 0
        self.context_info.self = self.context_info._addr
        self.context_info.unkptr_10 = 0
        self.context_info.push()

        self.gpu_context = agx.kobj.new(GPUContextData).push()

        self.ttbr0_base = self.u.memalign(self.agx.PAGE_SIZE, self.agx.PAGE_SIZE)
        self.p.memset32(self.ttbr0_base, 0, self.agx.PAGE_SIZE)

        self.objects = {}

        # 32K VA pages since buffer manager needs that
        self.uobj = GPUAllocator(agx, "Userspace", 0x1600000000, 0x100000000, ctx=None,
                                 guard_pages=1,
                                 va_block=32768, nG=1, AP=0, PXN=1, UXN=1)

    def bind(self, ctx_id):
        self.ctx = ctx_id
        self.uobj.ctx = ctx_id
        self.uat.bind_context(ctx_id, self.ttbr0_base)

    def make_stream(self, base):
        return self.uat.iostream(self.ctx, base)

    def new_at(self, addr, objtype, name=None, track=True, **flags):
        obj = GPUObject(self, objtype)
        obj._stream = self.make_stream
        if name is not None:
            obj._name = name

        size_align = align_up(obj._size, self.agx.PAGE_SIZE)
        obj._addr = addr

        obj._paddr = self.agx.u.memalign(self.agx.PAGE_SIZE, size_align)
        #if isinstance(obj.val, ConstructClassBase):
            #obj.val._addr = obj._addr

        print(f"[Context@{self.gpu_context._addr}] Map {obj._name} size {obj._size:#x} @ {obj._addr:#x} ({obj._paddr:#x})")

        self.agx.uat.iomap_at(self.ctx, obj._addr, obj._paddr, size_align, **flags)
        self.objects[obj._addr] = obj
        self.agx.reg_object(obj, track=track)

        return obj

    def buf_at(self, addr, is_pipeline, size, name=None, track=True):
        return self.new_at(addr, Bytes(size), name, track=track,
                           AttrIndex=MemoryAttr.Shared, PXN=1,
                           nG=1, AP=(1 if is_pipeline else 0))

    def load_blob(self, addr, is_pipeline, filename, track=True):
        data = open(filename, "rb").read()
        obj = self.new_at(addr, Bytes(len(data)), filename, track=track,
                          AttrIndex=MemoryAttr.Shared, PXN=1,
                          nG=1, AP=(1 if is_pipeline else 0))
        obj.val = data
        obj.push()

        return obj

class GPUWorkQueue:
    def __init__(self, agx, context):
        self.agx = agx
        self.u = agx.u
        self.p = agx.p
        self.context = context

        self.info = agx.kobj.new(CommandQueueInfo)

        self.pointers = agx.kshared.new(CommandQueuePointers).push()
        self.pmap = CommandQueuePointerMap(self.u, self.pointers._paddr)

        self.rb_size = self.pointers.rb_size
        self.ring = agx.kobj.new_buf(8 * self.rb_size, "GPUWorkQueue.RB")

        self.info.pointers = self.pointers
        self.info.rb_addr = self.ring._addr
        self.info.context_info = context.context_info
        self.info.gpu_buf_addr = agx.kobj.buf(0x2c18, "GPUWorkQueue.gpu_buf")
        self.info.gpu_context = context.gpu_context
        self.info.push()

        self.wptr = 0
        self.first_time = True

        self.agx.uat.flush_dirty()

    def submit(self, work):
        work.push()

        self.p.write64(self.ring._paddr + 8 * self.wptr, work._addr)
        self.wptr = (self.wptr + 1) % self.rb_size
        self.agx.uat.flush_dirty()
        self.pmap.CPU_WPTR.val = self.wptr

    def wait_empty(self):
        while self.wptr != self.pmap.GPU_DONEPTR.val:
            self.agx.work()

class GPU3DWorkQueue(GPUWorkQueue):
    TYPE = 1

class GPUTAWorkQueue(GPUWorkQueue):
    TYPE = 0

class GPUMicroSequence:
    def __init__(self, agx):
        self.agx = agx
        self.ops = []
        self.obj = None

    def append(self, op):
        self.ops.append(op)

    def finalize(self):
        self.ops.append(EndCmd())
        self.size = sum(i.sizeof() for i in self.ops)
        self.obj = self.agx.kobj.new_buf(self.size, "GPUMicroSequence")
        self.obj.val = b"".join(i.build() for i in self.ops)
        self.obj.push()
        return self.obj

    def dump(self):
        chexdump(self.agx.iface.readmem(self.obj._paddr, self.size))
        print(MicroSequence.parse_stream(self.agx.uat.iostream(0, self.obj._addr)))

    def __str__(self):
        s = f"GPUMicroSequence: {len(self.ops)} ops\n"
        for i, op in enumerate(self.ops):
            op_s = textwrap.indent(str(op), ' ' * 4)
            s += f"[{i:2}:{op.sizeof():#x}] = {op!s}\n"
        return s

class GPUBufferManager:
    def __init__(self, agx, context, blocks=8):
        self.agx = agx
        self.ctx = context

        self.block_ctl_obj = agx.kshared.new(BufferManagerBlockControl)
        self.block_ctl_obj.total = blocks
        self.block_ctl_obj.wptr = 0
        self.block_ctl_obj.unk = 0
        self.block_ctl = self.block_ctl_obj.push().regmap()

        self.counter_obj = agx.kshared.new(BufferManagerCounter)
        self.counter_obj.count = 1
        self.counter = self.counter_obj.push().regmap()

        self.misc_obj = agx.kshared.new(BufferManagerMisc)
        self.misc_obj.cpu_flag = 1
        self.misc = self.misc_obj.push().regmap()

        self.page_size = 0x8000
        self.pages_per_block = 4
        self.block_size = self.pages_per_block * self.page_size

        self.page_list = context.uobj.new(Array(0x10000 // 4, Int32ul), "BM PageList")
        self.block_list = context.uobj.new(Array(0x8000 // 4, Int32ul), "BM BlockList")

        self.info = info = agx.kobj.new(BufferManagerInfo)
        info.page_list_addr = self.page_list._addr
        info.page_list_size = self.page_list._size
        info.page_count = self.block_ctl_obj.total * 4
        info.block_count = self.block_ctl_obj.total

        info.block_list_addr = self.block_list._addr
        info.block_ctl = self.block_ctl_obj
        info.last_page = info.page_count - 1
        info.block_size = self.block_size

        info.counter = self.counter_obj
        info.misc = self.misc_obj

        info.unkptr_d8 = context.uobj.buf(0x80, "BufferManager unk")

        self.populate()
        self.block_ctl_obj.pull()
        self.block_list.push()
        self.page_list.push()

        info.push()

    def populate(self):
        idx = self.block_ctl.wptr.val
        total = self.block_ctl.total.val
        while idx < total:
            block = self.ctx.uobj.new_buf(self.block_size, "BM Block", track=False)
            self.block_list[idx] = block._addr // self.page_size

            page_idx = idx * self.pages_per_block
            for i in range(self.pages_per_block):
                self.page_list[page_idx + i] = block._addr // self.page_size + i

            idx += 1
        self.block_ctl.wptr.val = idx
