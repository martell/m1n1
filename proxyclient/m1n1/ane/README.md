
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

An ANE DT instance refers to a single neural processor circuit [2].
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

Regarding the multi-processor ane\*'s,
I only have a T8103 to study so I'm not 100% on this, 
but my understanding is that:

1) each device is an indepedent instance 
2) there's very minimal binary diffs in firmware 
3) .. without a central communication / sync mechanism 
4) T600X's don't leverge the multi-engines

My guess is that apple copy-pasted the processors and
realized concurrency was too hard / unecessary post-prod. 
AFAIK the mmio ranges I describe below hold true for the other engines,
so would be interesting to see if the idle silicons can be resuscitated...


### Specs

Each board (1 <= M <= 4) can have 8 or 16 (N) neural engines [2].
Each of the N engines have 256 MAD circuits (X = 256) [2]. This value seems constant.
For device with 1 board (M = 1), it can have 8 neural engines
which provides 1\*8\*256 (2,048) operations in each processing cycle [2].
For a device with two neural processor circuits (M = 2), with
sixteen neural engines (N = 16), it can provide up to 
2\*16\*256 (8,192) operations in each processing cycle [2]. 
The first is true for T8103. Specs are unclear for the others (TODO).

The MAC operates fixed INT8 or FP16 [2]. 
The same patent claims that each MAC has a 
*32-bit* accumulator (???) for intermediate buffers, 
specifically to serve as an "accumulated value 
for an addition operation with the multiplied value of a subsequent 
(e.g., next) processing cycle" [2]. 
This definitely has to do with the L2 cache (see memmap below),
which is not understood completely yet. 

IRQs (see "execution" later) are synced to a 24Hz clock. 



## MMIO Map

AKA "safe" ranges I bruteforced.
Offsets most likely hold true for other boards. 

    0x26a000000 - 0x26a001000 random tunables filled @ init, never again
    0x26b000000 - 0x26b010020 
    0x26b050000 - 0x26b0ffff0 
    0x26b100000 - 0x26b1ffffc 
    0x26b400000 - 0x26b457100 ane-asc base
    0x26b800000 - 0x26b808000 
    0x26b840000 - 0x26b854000 
    0x26b860000 - 0x26b870000 
    0x26b874000 - 0x26b875000 
    0x26b900000 - 0x26b90c200 performance, e.g. clock cycles, dma read bytes
    0x26bc04000 - 0x26bc28000 config
    0x26bc34000 - 0x26bc43ffc kmem
    0x26bd00000 - 0x26bf00000 l2 cache


## ASC

TODO


## Terminology

**task:** 
A task is an ANE's "op". 

**task descriptor (TD):**
A task is associated with a *task descriptor* 
that defines a configuration of neural processor circuit to execute the task [1]. 
Basically, a regfile describing the configuration registers. 
It has a specific format allowing the "TD fetcher DMA circuit"[1] to fetch it from 
sysmem & write to the registers for us. This isn't just a memcpy, it's smart:
it accounts for repeats, fills in address data (see BAR soon), calculates
next address offsets, etc. Each TD buf is 0x274 ish long. 


    struct task_sequence {
        dma_addr_t ts_buf;
        unsigned int td_count;
        unsigned int t0_size;
    };

**task sequence (TS):** 
Given a neural network, the frontend of Apple's compiler 
builds a DAG ast-like representation of the computation ops. 
This graph is transformed into a linear linked list of *tasks*, referred to as a *task sequence*. 
hence TS represents the complete neural network in a format executable by the neural processor circuit[1].
No upper limit on the number of tasks, but total size <0x10000. 

**head task descriptor (T0):**
The 0th index TD of a TS. 
Only this TD is used for populating & pushing the FIFO req pool. 


    struct engine_request {
        struct task_sequence *ts;
        unsigned int nid;
        dma_addr_t fifo_vaddr;
        dma_addr_t bar[0x20];
    };


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



[1] https://patentimages.storage.googleapis.com/09/94/b0/33e4247e137a73/US20220237438A1.pdf
[2] https://patentimages.storage.googleapis.com/86/1d/f1/8bdda8a34c5dc1/US20190340491A1.pdf
