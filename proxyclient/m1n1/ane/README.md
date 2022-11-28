
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


Neural processor circuit is a *programmable circuit* [1].
It is just a MADD unit at its core, but
using its vast configuration registers, 
which span the entire 0x4000 - 0x20000 range,
it can be configured/programmed to do many cool and exotic ops.


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


## FIFO

TODO



## Misc  

The enqueueing of a TQ and the writes to the "execution" regs are 
technically the job of the ASC firmware. 
However, I quickly figured out the 10-ish necessary writes and 
decided to do them myself. 
So currently asc is just being ignored. Fw's not even mapped.

- uses DART practically out of the box
- FP16 :(
- has its own DPE instance 
    - and a wall of init data I have yet to figure out



[1] https://patentimages.storage.googleapis.com/09/94/b0/33e4247e137a73/US20220237438A1.pdf
