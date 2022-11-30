
# ANE

## Introduction

From Apple themselves,

> Neural processor circuit is a circuit that 
> performs various machine learning operations based on 
> computation including multiplication, addition, and accumulation. 
> Neural processor circuit is a configurable circuit that
> performs these operations in a fast and power-efficient
> manner while relieving CPU of resource-intensive
> operations associated with neural network operations [1]


## Hardware

### Board types

A DT instance refers to a single neural processor circuit [2].
Here's the scraped DT nodes:

| Marketing name                      | Product | SoC   | ane device          | ane type |
|-------------------------------------|---------|-------|---------------------|----------|
| Mac mini (M1, 2020)                 | J274AP  | T8103 | ane                 | 64       |
| MacBook Pro (13-inch, M1, 2020)     | J293AP  | T8103 | ane                 | 64       |
| MacBook Air (M1, 2020)              | J313AP  | T8103 | ane                 | 64       |
| iMac (24-inch (4-port), M1, 2021)   | J456AP  | T8103 | ane                 | 64       |
| iMac (24-inch (2-port), M1, 2021)   | J457AP  | T8103 | ane                 | 64       |
| MacBook Pro (16-inch, M1 Pro, 2021) | J316sAP | T6000 | ane0                | 96       |
| MacBook Pro (16-inch, M1 Max, 2021) | J316cAP | T6001 | ane0,ane1           | 96       |
| MacBook Pro (14-inch, M1 Pro, 2021) | J314sAP | T6000 | ane0                | 96       |
| MacBook Pro (14-inch, M1 Max, 2021) | J314cAP | T6001 | ane0,ane1           | 96       |
| Mac Studio (M1 Max, 2022)           | J375cAP | T6001 | ane0,ane1           | 96       |
| Mac Studio (M1 Ultra, 2022)         | J375dAP | T6002 | ane0,ane1,ane2,ane3 | 96       |
| MacBook Pro (13-inch, M2, 2022)     | J493AP  | T8112 | ane                 | 128      |
| MacBook Air (M2, 2022)              | J413AP  | T8112 | ane                 | 128      |


| codename | firmware                   | dt (type) | mmio base    | pmu base + size       |
|----------|----------------------------|-----------|--------------|-----------------------|
| styx     | h13\_ane\_fw\_styx\_j5x    | ane (64)  | 0x26a000000  | 0x23b700000+0x8c000   |
| eos0     | t600x\_ane0\_fw\_eos\_jc3x | ane0 (96) | 0x284000000  | 0x28e080000+0xc02c    |
| eos1     | t600x\_ane1\_fw\_eos\_jc3x | ane1 (96) | 0x508000000  | 0x28e680100+0x3f2c    |
| eos2     | t600x\_ane2\_fw\_eos\_jc3x | ane2 (96) | 0x2284000000 | 0x228e080000+0xc02c   |
| eos3     | t600x\_ane3\_fw\_eos\_jc3x | ane3 (96) | 0x2508000000 | 0x228e680100+0x3f2c   |
| bia      | h14\_ane\_fw\_bia\_j4xx    | ane (128) | 0x26a000000  | 0x23b700000+0x18000\* |

\* two pmu ranges. 0x23b700000+0x18000 & 0x23b724000+0x4000.


### Multi-ANEs ??

I only have a T8103 in front of me so I'm not 100% on this, 
but regarding the multi-processor ane\*'s,
my understanding is that:

1) each device is an indepedent instance 
2) there's very minimal binary diffs in firmware 
3) .. without a central communication / sync mechanism 
4) T600X's don't leverge the multi-ane's

My guess is that apple copy-pasted the processors and
realized concurrency was too hard / unecessary post-prod. 
Backing this is the patent, titled "*Scalable* Neural Network Processing Engine", 
which says, "in some embodiments... multiple activated neural
processor circuits perform ... in parallel" [2]; immediately the next sentence
discusses "deactivated" processors for "power saving" mode [2]. 
Nothing more about multi-engines. Hmmm.
AFAIK the MMIO ranges (described below) hold true for the other boards,
so would be interesting to see if the idle silicons can be resuscitated...


### Specs

Each board (1 <= M <= 4) can have 8 or 16 (N) neural engines [2].
Each of the N engines have 256 MADD circuits (X = 256) [2]. This value seems constant.
For device with 1 board (M = 1), it can have 8 neural engines
which provides 1\*8\*256 (2,048) operations in each processing cycle [2].
For a device with two neural processor circuits (M = 2), with
sixteen neural engines (N = 16), it can provide up to 
2\*16\*256 (8,192) operations in each processing cycle [2]. 
The first is true for T8103. Specs are unclear for the others (TODO).

The MAC operates fixed INT8 or FP16 [2]. 
The same patent claims that each MAC has a 
*32-bit* accumulator (??) for intermediate buffers, 
specifically to serve as an "accumulated value 
for an addition operation with the multiplied value of a subsequent 
(e.g., next) processing cycle" [2]. 
The relation to L2 (see L2 section) is not really 
understood, and where the 32 would come from then.

IRQs (see "execution" later) are synced to a 24Hz clock. 


## MMIO Map

"Safe" ranges I bruteforced within the entire 0x2000000 container.
Offsets most likely hold true for other boards. 
~~Importance in descending order~~

    0x26a000000 - 0x26a001000 random tunables filled @ init, never again
    0x26b000000 - 0x26b010020 random asc data  
    0x26b050000 - 0x26b1ffffc asc [a]
    0x26b400000 - 0x26b457100 asc mailbox [b]
    0x26b800000 - 0x26b808000 dart0, dart3 (0x4000 each)
    0x26b810000 - 0x26b814000 dart1 
    0x26b820000 - 0x26b824000 dart2 
    0x26b840000 - 0x26b854000 asc irq / doorbell [c]
    0x26b860000 - 0x26b870000 gpio for acks w/ asc; "let's meet here"
    0x26b874000 - 0x26b875000 nada
    0x26b8ec000 - 0x26b8efffc dpe ppt (?) data 
    0x26b8f0000 - 0x26b8f3ffc dpe sys tunables / data [d]
    0x26b8f4000 - 0x26b875000 dpe soc tunables / data [d]
    0x26b900000 - 0x26b90c200 performance reports, e.g. DMA read bytes
    0x26bc04000 - 0x26bc28000 computation engine [e]
    0x26bc34000 - 0x26bc44000 krn L2 cache
    0x26bd00000 - 0x26bf00000 tile L2 cache

[a] 0x1050000 is RVBAR. Protip: if you mess with this region while running a coreml model under the hypervisor, the kext straight up fails and dumps (log show --last 5m) the names of ASC/CPU IMPL regs in the very region. Talk about irony. Fans go screeching tho. Also some free-running 24hz clocks in the upper region engine cycles sync to.

[b] maps to [HW:ASC](https://github.com/AsahiLinux/docs/wiki/HW:ASC) somewhat, so mailbox stuff. HOWEVER, this "mailbox" isn't used for communication (see ASC below).

[c] hard-coded acks. version code at the top. probably not much different than the gpio's right below it.

[d] default tunables filled in at boot. these are constant and retain state.

[e] from this point on is the "computation engine", as expanded in the next section. 



## Computation Engine

Like other components on the M1, there's an ASC (logs call it "ANE CPU") running firmware
*faciliating* the computation. This section deals not with the ASC's role/interface, but 
how the "neural processor circuit" does the *actual* computation. 
I'm calling this collectively the "engine".

    0x26bc04000 - 0x26bc20000 MADD configuration
    0x26bc20000 - 0x26bc24000 DMA configuration
    0x26bc24000 - 0x26bc25000 task manager 
    0x26bc25000 - 0x26bc28000 task queues 
    0x26bc34000 - 0x26bc44000 kernel memory
    0x26bd00000 - 0x26bf00000 tile L2 cache

### Overview

The core computation engine is just a MADD unit. 
At a high-level, the engine takes input and passes it through the MADDs
to generate output.
The engine is not smart. 
When the "trigger" register is written to, it will "push" 
(a single pass through the MADDs) with whatever the current state says. 
There's no predefined primitive unit (e.g. shader), 
hence no ISA that operates on those. 
Its "work unit", at best, 
is a 0x4000 tile of IEEE 754 packed floats.

To quote apple again,

> Neural processor circuit is a *configurable circuit* 
> that performs neural network operations on the 
> input data based at least on kernel data [3]

The fundamental model is a [2D/image convolution](https://stats.stackexchange.com/a/335327), 
which is a sum of the products (ah, see where MADD comes in) 
of an input matrix against a "sliding window" (kernel). 
All other "modes" (e.g. element-wise, concat, matrix multiplication) 
are secretly a ***convolution shaped in a funny way***
s.t. it is represented as a **MADD pass through the engine**.
For example, a (N, M) matrix multiplication is reshaped as a 
convolution with 1x1 shaped kernel data with M input channels and L output channels
(see [4] for more reading and 
ane_matmul2d.py where the input matrix is copied for the broadcasting trick). 
Restated,

1) Various "modes" of operation are just certain *configurations* of the engine.  
2) The "secret" to all those exotic neural network ops lie in the
0x26bc04000 - 0x26bc20000 configuration registers
3) There is no difference in executing a basic convolution vs. batched 3D pooled ellipse kernel acosh hyper-relu-whatever lstm as long as it is compiled to the fundamental model.


## Terminology

**task:** 
A task is an ANE's "op". 

**task sequence (TS):** 
Given a neural network, the frontend of Apple's compiler 
builds a DAG ast-like representation of the operations. 
This graph is transformed into a linear linked list of *tasks*, collectively a *task sequence*. 

**task descriptor (TD):**
A task is associated with a *task descriptor* 
that defines a configuration of neural processor circuit to execute the task [1]. 
AFAIK each TD is 0x274 or 0x278 long depending on whether the header is 28 or 32 long. 
TD has a certain encoding expected by the TD fetcher circuit (see DMA soon). 
It has these fields:

| kernel     | common     | src tile   | dst tile   | L2         | planar     | neural     |
|------------|------------|------------|------------|------------|------------|------------|
| 0xf401f800 | 0x3c000000 | 0x6c013800 | 0x44004800 | 0x0c008800 | 0x1000c800 | 0x18017800 |


TLDR, a task is a pass on the ANE. 
TD is a binary file describing the state of the configuration registers in that pass. 
A full neural network often can't be dumbed down to a single pass,
so it sequence of them are passed around instead. 
Thus, TS represents the complete neural network in a 
format executable by the neural processor circuit [1]. 


## DMA

Thankfully, there's no crazy memory management.
It uses DART practically out-of-the-box. 
Anything DMA deals with DART-translated virtual addresses, 
which the (not image) kernel is in full control of.
Address stuff & how these are coupled is discussed in depth in 
*Scheduling* (specifically BAR). 
There are 4 DMA circuits for IO between sysmem/hw, each with its own role:

**1) Kernel Fetcher**:
One job: given the vaddr in the kernel_vaddr register, memcpy's it to the 
kernel memory (see L2). Can be ~~any~~ 0 <= x <= 0x10000 (region size) 8b-aligned size.

**2) Input Tile Fetcher**:
*Dynamically determined number of* job(s): given the vaddr(s) in the src(N) register(s), memcpy's it to L2. Operates on the basis of tiles, so must be aligned to the tile size (0x4000). 

**3) Output Tile Sender**:
Same as above, but other way around.
Still investigating whether/how multiple output tiles are supported.

**4) TD Fetcher**:
Note that the configuration registers (0x26bc04000 - 0x26bc20000)
are never touched directly. That would be both expensive and error-prone.
The TD fetcher handles it for us. 
Recall the TD codes; (mostly) the upper half for the length of the
subsequent stream of values & lower half for the offset (from 0x26bc00000),
which the fetcher broadcasts it accordingly. There are lots of 
adjustments though; notice how the TD buffer supposedly fills up something 200x its size?
TD encodes many more special broadcasts/repeats/exceptions, 
for example the "common" field gets copied to -0x800 before the others 
(notice the lower is 0x0000 which isn't accessible). 

Fun fact: I reversed the entire TD broadcasting 
process *and* wrote a driver for the subsequent writes before realizing it 
wasn't me doing the work. 
I commented out a wrong line and still saw the config range fill up, 
thought I was going insane, and ended up doing a new os install.
Randomly replaced a BAR addr with 0xCAFEBABE, and 
saw it magically broadcast to my reversed locations.
Figured out BAR within the next hour and everything started to make sense.


## L2 / kmem

The engine has its own L2 cache (not asc's L2, that's separate),
which is just a chunk of the MMIO region. 
Think of it as an intermediate work space.
The following is the region in midst of a batched pass; 
input (uniform 2222 matrix for clarity) first populates the region. See how the 
sections are accumulating to 3e8b:

    000000026bd003a0 22222222 22222222 22222222 22222222 22222222 22222222 22222222 22222222
    000000026bd003c0 22222222 22222222 22222222 22222222 22222222 22222222 22222222 22222222
    000000026bd003e0 22222222 22222222 22222222 22222222 22222222 22222222 22222222 22222222
    000000026bd00400 3e8b3e8b 3e8b3e8b 3e8b3e8b 3e8b3e8b 3e8b3e8b 3e8b3e8b 3e8b3e8b 3e8b3e8b
    000000026bd00420 3e8b3e8b 3e8b3e8b 3e8b3e8b 3e8b3e8b 3e8b3e8b 3e8b3e8b 3e8b3e8b 3e8b3e8b
    000000026bd00440 3e8b3e8b 3e8b3e8b 3e8b3e8b 3e8b3e8b 3e8b3e8b 3e8b3e8b 3e8b3e8b 3e8b3e8b
    000000026bd00460 3e8b3e8b 3e8b3e8b 3e8b3e8b 3e8b3e8b 3e8b3e8b 3e8b3e8b 3e8b3e8b 3e8b3e8b
    000000026bd00480 3e8b3e8b 3e8b3e8b 3e8b3e8b 3e8b3e8b 3e8b3e8b 3e8b3e8b 3e8b3e8b 3e8b3e8b
    000000026bd004a0 3e8b3e8b 3e8b3e8b 3e8b3e8b 3e8b3e8b 3e8b3e8b 3e8b3e8b 3e8b3e8b 3e8b3e8b
    000000026bd004c0 22222222 22222222 22222222 22222222 22222222 22222222 22222222 22222222
    000000026bd004e0 3e8b3e8b 3e8b3e8b 3e8b3e8b 3e8b3e8b 3e8b3e8b 3e8b3e8b 3e8b3e8b 3e8b3e8b
    000000026bd00500 22222222 22222222 22222222 22222222 22222222 22222222 22222222 22222222
    000000026bd00520 3e8b3e8b 3e8b3e8b 3e8b3e8b 3e8b3e8b 3e8b3e8b 3e8b3e8b 3e8b3e8b 3e8b3e8b
    000000026bd00540 22222222 22222222 22222222 22222222 22222222 22222222 22222222 22222222
    000000026bd00560 3e8b3e8b 3e8b3e8b 3e8b3e8b 3e8b3e8b 3e8b3e8b 3e8b3e8b 3e8b3e8b 3e8b3e8b
    000000026bd00580 22222222 22222222 22222222 22222222 22222222 22222222 22222222 22222222

This region is *never* touched by anyone else. It's not designed to be managed. 
The engine, upon receiving a new input, simply overwrites it. 
Here's it after another cycle (input 4500 & output 5500), purposely shaped smaller,
overwriting the previous:

    000000026bd00100 55005500 55005500 55005500 55005500 55005500 55005500 55005500 55005500
    000000026bd00120 55005500 55005500 55005500 55005500 55005500 55005500 55005500 55005500
    000000026bd00140 22222222 22222222 22222222 22222222 45004500 45004500 00000000 00000000
    000000026bd00160 55005500 55005500 55005500 55005500 55005500 55005500 55005500 55005500
    000000026bd001a0 55005500 55005500 55005500 55005500 55005500 55005500 55005500 55005500
    000000026bd001e0 55005500 55005500 55005500 55005500 55005500 55005500 55005500 55005500
    000000026bd00220 55005500 55005500 55005500 55005500 55005500 55005500 55005500 55005500
    000000026bd00240 22222222 22222222 22222222 22222222 45004500 45004500 00000000 00000000
    000000026bd00340 22222222 22222222 22222222 22222222 45004500 45004500 00000000 00000000
    000000026bd00440 3e8b3e8b 3e8b3e8b 3e8b3e8b 3e8b3e8b 45004500 45004500 00000000 00000000

Kernel memory behaves similarly but is not a "work region". 
It's just a place for the kernel data to reside. It also gets overwritten.


## Terminology

**request:**
neural engine's unit of execution.

**Neural ID (NID):**
identifier constant for a request. 0x00 < nid < 0xff. 
Used for 1) identifying the TD in a TS 2) identifying a TS in a pool of FIFO requests.   

**Base Address Resolution (BAR):**
A 0x20 arr/list/table of virtual addresses. 
Of the many config regs, there are ones for address, 
e.g. tile destination buffer address register. 
These are zeroed out by the compiler (for good reason). 
Instead of ever manually manipulating those, 
Apple nicely hooked a circuit (this will make sense in a moment)
s.t. the values in BAR are dma'd to their appropriate positions in the config regs.
It even calculates the offsetted addrs (e.g. destination next addr).
BAR has a set order (e.g. td_ptr->krn_ptr->src1_ptr) to make address oopsies hard. 
Note that BAR[0] is always the dva to the TS buffer.



## Scheduling

The Task Manager (TM) operates on the basis of queues. 
Each Task Queue (TQ) is a hardware slot, and there's 8 of them. 
See FIG 10 of [1].
A TQ is basically a "waiting room" 
for a single request before it is "arbitered" by the TM to to be executed.
Looking at the structure of a TQ below, you can see how it is
designed to encapsulate a *task*
(familiar words like BAR and NID, eh?)


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


To execute a queue from the pool of 8, three registers at the top of 
the TM regs are written with the request & queue_id values. 
This will actually trigger the circuit to push the request.
TM is supposed to do fancy scheduling & arbitering stuff with the TQ's and 
priority parameters (e.g. async execution / data dependence stuff),
but that stuff is rarely used. 


The enqueueing of a TQ and the writes to the "execution" regs are 
technically the job of the ASC firmware. 
However, I quickly figured out the 10-ish necessary writes and 
decided to do them myself. 
So currently asc is just being ignored. Fw's not even mapped.


## FIFO

TODO


## TODO

- see what happens if unmapped addr is placed in BAR
- pattern for kmem overwrites



## Sources

[1] [TASK CONTEXT SWITCH FOR NEURAL PROCESSOR CIRCUIT](https://patentimages.storage.googleapis.com/86/1d/f1/8bdda8a34c5dc1/US20190340491A1.pdf)

[2] [SCALABLE NEURAL NETWORK PROCESSING ENGINE](https://patentimages.storage.googleapis.com/09/94/b0/33e4247e137a73/US20220237438A1.pdf)

[3] ) DYNAMICALLY SHAPING AND
SEGMENTING WORK UNITS FOR
PROCESSING IN NEURAL NETWORK
PROCESSOR


[4] https://patentimages.storage.googleapis.com/b9/db/be/52e7a45d4cafd5/US20190340486A1.pdf