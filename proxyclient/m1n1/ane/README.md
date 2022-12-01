
# ANE

## Introduction

From Apple themselves,

> Neural processor circuit is a circuit that 
> performs various machine learning operations based on 
> computation including multiplication, addition, and accumulation.
> Neural processor circuit is a configurable circuit that
> performs these operations in a fast and power-efficient
> manner while relieving CPU of resource-intensive
> operations associated with neural network operations[1]


## Hardware

### Board types

Each neural processor has its own DT instance.
Here's the scraped DT nodes for each SoC:

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


More on each board variant:

| codename | firmware                   | dt (type) | mmio base    | pmu base + size       |
|----------|----------------------------|-----------|--------------|-----------------------|
| styx     | h13\_ane\_fw\_styx\_j5x    | ane (64)  | 0x26a000000  | 0x23b700000+0x8c000   |
| eos0     | t600x\_ane0\_fw\_eos\_jc3x | ane0 (96) | 0x284000000  | 0x28e080000+0xc02c    |
| eos1     | t600x\_ane1\_fw\_eos\_jc3x | ane1 (96) | 0x508000000  | 0x28e680100+0x3f2c    |
| eos2     | t600x\_ane2\_fw\_eos\_jc3x | ane2 (96) | 0x2284000000 | 0x228e080000+0xc02c   |
| eos3     | t600x\_ane3\_fw\_eos\_jc3x | ane3 (96) | 0x2508000000 | 0x228e680100+0x3f2c   |
| bia      | h14\_ane\_fw\_bia\_j4xx    | ane (128) | 0x26a000000  | 0x23b700000+0x18000\* |

\* two pmu ranges. 0x23b700000+0x18000 & 0x23b724000+0x4000.


### Specs

Each board (1 <= M <= 4) can have 8 or 16 (N) neural engines [2].
Each of the N neural engines have 256 MADD circuits (X = 256) [2]. 
This value seems constant.
For device with 1 board (M = 1), it can have 8 neural engines
which provides ``1*8*256 = 2048`` operations in each processing cycle [2].
For a device with two neural processor circuits (M = 2), with
sixteen neural engines (N = 16), it can provide up to 
``2*16*256 = 8192`` operations in each processing cycle [2]. 
The first is true for T8103. Specs are unclear for the others (TODO).


### Multi-ANEs ??

I only have a measly T8103 in front of me so I'm not 100% on this, 
but regarding the multi-processor ane[0-3]'s,
my understanding is that:

1) each processor is an indepedent instance 
2) there's very minimal binary diffs in firmware 
3) .. without a central communication / sync mechanism 
4) T600X's don't leverge the multi-ane's

My guess is that apple copy-pasted the processors and
realized concurrency was too hard / unecessary post-prod. 
Backing this is the patent introducing the architecture:
"in some embodiments... multiple activated neural
processor circuits perform ... in parallel" [2]; 
Immediately the next sentence 
discusses "deactivated" processors for "power saving" mode [2]. Hmmm.
AFAIK the MMIO ranges (described below) hold true for the other boards,
so would be interesting to see if the idle silicons can be resuscitated...



## MMIO Map

"Safe" ranges I bruteforced within the entire 0x2000000 container.
Offsets most likely hold true for other boards. 
~~Importance in descending order~~

    0x26a000000 - 0x26a001000 random tunables filled @ init
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
    0x26bc04000 - 0x26bc28000 engine [e]
    0x26bc34000 - 0x26bc44000 kernel L2 cache [f]
    0x26bd00000 - 0x26bf00000 tile L2 cache

[a] 0x1050000 is RVBAR. Protip: if you mess with this region while running a coreml model under the hypervisor, the kext straight up fails and dumps (``log show --last 5m``) the names of ASC/CPU IMPL regs in the very region. Ironic. Also some free-running 24hz clocks in the upper region the engine cycles sync to.

[b] maps to [HW:ASC](https://github.com/AsahiLinux/docs/wiki/HW:ASC) somewhat, so should be mailbox stuff. however, this is either not mailbox or it's just not used for communication

[c] these are the regs used for communication. I don't think it's wired to asc? More similar to the gpio regs right below it? 

[d] default tunables filled in at boot. these are constant and retain state.

[e] from this point on is the "computation core", as expanded in the next section. 

[f] there's the [Kernel (operating system)](https://en.wikipedia.org/wiki/Kernel_(operating_system)) and [Kernel (image processing)](https://en.wikipedia.org/wiki/Kernel_(image_processing)). The former will be referred to as "kernel-side". 
So, the latter here.


## Computation Core

Like other components on the M1, there's an ASC (logs call it "ANE CPU") running firmware
*faciliating* the computation. This section deals not with the ASC's role/interface, but 
how the processor does the *actual* computation. MMIO map:

    0x26bc04000 - 0x26bc20000 MADD configuration
    0x26bc20000 - 0x26bc24000 DMA configuration
    0x26bc24000 - 0x26bc25000 task manager 
    0x26bc25000 - 0x26bc28000 task queues 
    0x26bc34000 - 0x26bc44000 kernel L2 cache
    0x26bd00000 - 0x26bf00000 tile L2 cache



### Convolution

Motivated by CNNs, the ANE was designed to accel
[2D/image convolution](https://stats.stackexchange.com/a/335327), 
which is a *sum of the products* of an input matrix within a "sliding window" (kernel). 
Accordingly, the computation core is a 
multiply-add (MADD) unit (recall X = 256 MADD circuits)
similar to many DSP/ISPs. 

A high-level overview of an operation: 
each MADD is first loaded with the kernel coefficients; input is pushed through the MADDs;
the input value and the corresponding kernel coefficient are multiplied
within the MADD to generate a processed value [5].
There's no predefined primitive unit (e.g. shader), 
hence no ISA that operates on those; 
its "work unit", at best, is a 0x4000 tile of IEEE 754 packed floats.
When the signalled at the control register,
it will literally push forward with whatever's in the current state.



### .maddrc

> Neural processor circuit is a *configurable circuit* 
> that performs neural network operations on the 
> input data based at least on kernel data [3]

Macos' compiler (and my minimal prototype :P) 
supports many cool operations 
other than the default convolution e.g.
element-wise mode or matrix multiplication. 
The core doesn't change though:
the "other" ops are secretly a ***convolution shaped in a funny way***
s.t. the operation is represented as a **MADD pass**. 
For example, a (NxM) @ (MxL) matrix multiplication 
is reformatted as the convolution of 
each N-dim slice of the (W=N, H=1, C=M) input 
with a 1x1 shaped kernel data with (Cin=M, Cout=L)[4];
this "instruction" is achieved by 
**setting the MADD configuration registers**\*
with fields like the new data size to fetch, 
total batch count to repeat for, 
a signal for the accumulator to "hold on" to the
slices in L2 until all slices are done, etc. 
Restated,

1) The ANE is a programmable / configurable MADD based on 2D convolutions
2) At the manager level, there is not much difference in executing a basic convolution vs. batched 3D pooled ellipse kernel hyper-relu-whatever acosh lstm (assuming it can be compiled... See TD!)


### L2

The engine has its own L2 cache (not asc's L2, that's separate),
located in the last remaining chunk of MMIO space. 
It functions as a fast & temporary intermediate work space.
The following is the region in midst of a batched pass; 
an input matrix of 2222, first populates the region; with the push,
the slices of the region are accumulating to the output (3e8b).

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

L2 is *never* touched. That's the DMA fetchers' job and it's clearly not meant to be managed: 
upon receiving a new input, the engine simply overwrites the values leftover from the previous cycle. 
Here's it after another pass  with input 4500 & output 5500, both purposely shaped smaller to demonstrate the temporary nature:

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

Kernel data has its own space; unlike tile L2, it's never operated on and 
it's read-only (since there's no kernel data being sent back). 
It's just a place for the kernel data to reside. It also gets overwritten.



## TD 

A **task** is a pass on the ANE. 
A task is associated with a **task descriptor**
that defines a configuration of neural processor circuit to execute the task [1]. 
A TD is a binary file describing the state of the configuration registers. 
TD has a certain encoding expected by the TD fetcher circuit (will see in DMA section soon). 
As of T8103, the *fields* of a TD, 
which are continuous "sections" of the config regs with a set function, along with
their codes, is as follows:


| Kernel     | Common     | Src        | L2         | Planar     | Neural     | Dst        |
|------------|------------|------------|------------|------------|------------|------------|
| 0xf401f800 | 0x3c000000 | 0x6c013800 | 0x44004800 | 0x0c008800 | 0x1000c800 | 0x18017800 |


Illustrated as 1204X of FIG12 of [1],
each field has a code encoding a 
"Register Count" and "Register Address", specifically [31:24] and [23:0]; 
e.g. field "src" has has 0x6c-many stream of registers starting from offset 0x13800.
The base for this offset is +0x1c00000 mmio space (0x26bc00000).
Since the header is always 0x28 or 0x32 long [1], and
``0xf4 + 0x3c + 0x6c + 0x44 + 0x0c + 0x10 + 0x18 + (0x7 * 8) = 0x24c``,
a TD must always be 0x274 or 0x278, which has been the case.

So far described a single TD. 
A full neural network, or a slightly complex one like my
matmul example from above, 
often requires more than a single pass. 
Multiple tasks are chained as a 
linear linked-list of tasks [6], denoted a *task sequence* (TS). 
TS thus represents the complete neural network in a 
format executable by the neural processor circuit [1]. 
Example TS buffer for batched matmuls: 

    00004000: 00000000 009c0000 00000400 00000000  ................ start of TD 0
    00004010: 00000068 00000000 30009800 00000300  h..........0....
    00004020: 02824026 00000000 f401f800 00000000  &@.............. kernel (f401f800)
    00004030: 00000000 00000080 00000080 00000080  ................ ] stream of vals f4 times
    00004040: 00000080 00000080 00000080 00000080  ................ 
    00004050: 00000080 00000080 00000080 00000080  ................
    00004060: 00000080 00000080 00000080 00000080  ................
    00004070: 00000080 00000000 00000000 00000000  ................ 
    000040b0: 00000000 00000040 00000040 00000040  ....@...@...@...
    000040c0: 00000040 00000040 00000040 00000040  @...@...@...@... ] stuff like kernel size
    000040d0: 00000040 00000040 00000040 00000040  @...@...@...@... ] is encoded here
    000040e0: 00000040 00000040 00000040 00000040  @...@...@...@...
    000040f0: 00000040 00000080 00000080 00000080  @...............
    00004100: 00000080 00000000 00000000 00000000  ................
    00004120: 00000000 3c000000 00030004 00000001  .......<........ common (3c000000)
    00004130: 00000022 00000002 00000002 00030004  "...............
    00004140: 00000001 5000a021 00002041 00014003  ....!..PA ...@..
    00004150: 00000003 00000000 00000000 04091101  ................
    00004160: 00100000 00000000 6c013800 00033881  .........8.l.8.. src (6c013800)
    00004170: 00008880 00000000 00000040 000000c0  ........@.......
    00004180: 00000180 00000180 00000000 00000000  ................
    000041a0: 00000000 01002031 00000000 00000100  ....1 ..........
    000041d0: 00000000 00000000 00000000 44004800  .............H.D l2 (44004800)
    000041e0: 00000000 00500172 00000000 00000010  ....r.P.........
    000041f0: 00000020 00000020 00000020 00000000   ... ... .......
    00004210: 0050017a 00000060 00000000 00000000  z.P.`...........
    00004220: 00000000 00000000 0c008800 00000000  ................ neural (0c008800)
    00004230: 00000000 00000000 00000000 1000c800  ................ planar (1000c800)
    00004240: 00000082 00101c0c 00000000 00000000  ................
    00004250: 00003c00 18017800 040000c1 00000180  .<...x.......... dst (18017800)
    00004260: 00000040 000000c0 00000300 00000300  @...............
    00004270: 01302031 00000000 00000000 00000000  1 0.............
    00004300: 03000001 00000000 00000422 00000000  ........"....... next TD @ roundup 0x100
    00004310: 0000006a 00000000 30009800 00000000  j..........0....
    00004320: 02024025 00000000 f401f800 00000000  %@.............. kernel, again (f401f800)
    00004330: 00000000 00000080 00000080 00000080  ................


You might have heard some people talking about a ".hwx" file.
This is that. However, information I've come across have
been incorrect and lacking research. 
So I would not trust / use it, if any.



## DMA

Change of pace from phys addrs to virtual addrs now.
Thankfully, ANE does not use some crazy memory management unit.
It uses DART practically out-of-the-box. 
Anything DMA exclusively uses *DART-translated virtual addresses*, 
which is fully controlled by the kernel-side;
addresses are discussed in depth in the Task Manager section.
There are 3 DMA circuits for IO between sysmem-hardware, 
each responsible for a specific buffer type:


**1) Kernel Fetcher**:
Kernel DMA is a read circuit that fetches kernel
information from system memory and sends kernel information
to each of the N neural engines [5]; 
Note that kernel is never sent back (read-only).
The kernel fetcher is coupled to a "kernel extract circuit"
which does LUT resolution iff the kernel is 
compressed [5], but I haven't got to that yet. 
For normal cases, it just memcpy's it to the kernel L2 space. 
Can be 0 <= x <= 0x10000 (range ceil) 8-aligned size,
opposed to a *tile* discussed now:


**2) Tile Fetcher**:
Includes a 1) read circuit that receives a
portion (e.g., tile) of the input data from
[system memory], for storing in data buffer (L2),
and a write circuit that forwards data from data buffer (L2)
to a target (e.g. system memory) [5]. 
Note: operates on the basis of tiles, 
so must be aligned to the tile size (0x4000).
Also a "normal" DMA circuit in that it just memcpy's 
to the L2 tile region. 


**3) TD Fetcher**:
We are slowly approaching the final boss of *Task Manager*,
which is an essay on its own, so lots of stuff is emitted.
Important to remember: configuration registers 
(both MADD (0x26bc04000 - 0x26bc20000) and DMA (0x26bc20000 - 0x26bc24000))
are ***never ever*** touched directly. 
That would be both expensive and error-prone. 
Instead, the TD fetcher handles it for us. 

The TD fetcher is responsible for transferring
the TD from sysmem to hardware, just like the above two.
However, remember the TD codes? 
Or notice how the tiny TD buffer is 
supposedly responsible for configuring a space 200x its size?
This transfer isn't just a memcpy, but a pretty 
complex read + parse + broadcast. 
Beyond parsing of the 7 fields, which is a task (pun) on its own,
TD encodes many more special broadcasts/repeats/exceptions;
for example, the "common" field has "offset" of 0x0000, which 
is inaccessible; instead, there's a rule that it gets 
copied to -0x800 before each of the other 6 fields 
(hence the name common and why those offsets all end in 0x800).

In reality, you don't need to know any of this 
as all the complexity is abstracted by the TD fetcher.
But why do I know this? -- I reversed the entire TD broadcasting 
and was doing "writes" myself before realizing it wasn't me doing the work. 
I commented out a wrong line and still saw the config range somehow fill up, 
thought I was going insane, even ended up doing a fresh os install. 
Replaced a BAR addr with 0x1234567, and 
saw it "magically" broadcast to my reversed locations.
Figured out BAR within the next hour and everything started to make sense.
Outsmarted by a circuit...



## Task Manager

> Neural task manager manages the overall
> operation of neural processor circuit. 
> Neural task manager may receive a task list 
> from a compiler executed by CPU, store tasks in its task queues, 
> choose a task to perform, and send task commands to 
> other components of the neural processor circuit 
> for performing the chosen task [1]

Task Manager operates on its 8 children task queues (TQ). See FIG 10 of [1].
Each TQ is a hardware slot of 0x148 width;
0x148\*8\*4 + 0x25000 (tq base) = 0x27900, stops right before restricted 
area of 0x28000. Each TQ encapsulates a single TS. 
Actions discussed above (DMA fetch, push through MADD)
are initiated when the Task Manager selects (arbiters)
one of the queues into the main queue. Basically, a "waiting room".
Each TQ includes a (1) header, which includes fields like status (in use?), 
priority, free slot count, etc, general information for the queue itself,
and (2) BAR:


### BAR

Base Address Resolution. TD fetcher will make sense now.
Of the many config regs, there are ones for IO. 
When the compiler (fully CPU btw) "allocates" to L2, 
it just fills out the "Yes, there's a buffer to fetch" field. 
Registers indicating buffer addresses, e.g. 
the output tile address register somewhere
in the "dst" range, are zeroed at compilation. 
The runtime-determined dva's must head to that register
somehow though -- instead of manually operating on addrs, 
apple nicely hooked a circuit that does it for us.

BAR is a FIFO hardware for storing of up to 0x20 virtual addresses. 
When a queue is selected to the main queue (by writing
a val generated from a function of queue_id into the main reg), 
DMA fetchers are signalled to fetch necessary input from that queue_id
before anything else (duh). The first is always TD fetcher; 
TD contains information on the other inputs, so it's always first. 
TD fetcher fetches from the 
vaddr stored in index 0 of the BAR of the selected queue. 
It then broadcasts the first TD of the fetched TS across the config regs.
Using that information (e.g. there is a kernel, no intermediate, and 2 src tiles)
and with dvas 1-by-1 indexed (and dequeued) from the remaining BAR table, 
1) writes the dva to their appropriate config reg and 
2) inits the appropriate DMA circuit to fetch from that dva into L2. 

Hence BAR has a specific order (td_ptr->krn_ptr->src1_ptr, etc.). 
TD Fetcher even calculates (and writes) the 
necessary offsetted addrs (e.g. kernel next addr after shifting) and does the addr arithmetic + writes too. 
All it takes is BAR order to not be f'ed up 
to make dynamic buffer allocs a lot less painless.
A very unique and nice feature IMO.



## ASC

The enqueueing of a TQ and the selection to the main queue 
are technically the asc's job. 
Under macos the engine regs are not touched by CPU. 
I can reliably boot the core to RVBAR, but I had major 
issues talking with the firmware after it booted. 
Either my faulty init data or other processor dependency issues.
However, so much of the heavy lifting is wired-in and
and I decided it was quicker to figure out task manager
before fighting the firmware any longer. 
So currently, asc is just being ignored. The firmware's not even mapped.
I could turn on the core, leave it at the half-init state (or not)
and it would not affect the experiments. 



## Sources

[1] [TASK CONTEXT SWITCH FOR NEURAL PROCESSOR CIRCUIT](https://patentimages.storage.googleapis.com/86/1d/f1/8bdda8a34c5dc1/US20190340491A1.pdf)

[2] [SCALABLE NEURAL NETWORK PROCESSING ENGINE](https://patentimages.storage.googleapis.com/09/94/b0/33e4247e137a73/US20220237438A1.pdf)

[3] [DYNAMICALLY SHAPING AND SEGMENTING WORK UNITS FOR PROCESSING IN NEURAL NETWORK PROCESSOR](https://patentimages.storage.googleapis.com/a4/83/a8/ad9d221cb7f8d8/US20190340498A1.pdf)

[4] [PERFORMING MULTIPLY AND ACCUMULATE OPERATIONS IN NEURAL NETWORK PROCESSOR](https://patentimages.storage.googleapis.com/b9/db/be/52e7a45d4cafd5/US20190340486A1.pdf)

[5] [COMPILING AND SCHEDULING TRANSACTIONS IN NEURAL NETWORK PROCESSOR](https://patentimages.storage.googleapis.com/42/7a/1f/099ed131b235f8/US11340936.pdf)

[6] [SYSTEMS AND METHODS FOR TASK SWITCHING IN NEURAL NETWORK PROCESSOR](https://patentimages.storage.googleapis.com/f5/fd/4b/ba09d9f878657f/US20190340014A1.pdf)
