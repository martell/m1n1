
# ANE 

Kernel side (not to be confused with image kernel),
i.e. work submission interface, constitutes the majority of this work.
DART works out of the box with just a few tweaks.
Power, as wonky as it looks, has proven very reliable 
(hence I haven't worked on it much).
My main work, TaskManager, has sofar piped tasks to hardware 
without much complaints.
Some interrupt data raised post-execution is not understood but 
it is performance/status information from the execution,
e.g. the timestamp pushed (not sure what it's exactly referring to though).
The actual computation results are dma'd to vmem though (if told to). 

That being said, the 
**entire** 0x4000 - 0x20000 range of configuration registers,
which I denote "td magic", is poorly understood.
This region is the expansion of a userspace compiler "regfile"
that does not invoke hardware 
(macos goes **great, great** lengths to determine hw board type because
***it's not in the device tree. jesus***).
P much summarizes my experience with the ANE.
Usually about 0x280-0x300, with a hard cap @ <0x1000. 
This does tie into BAR (base address resolution? register?) because it has
to dynamically adjust for input/intermediate/output buf count. 
The plain f(input1, input2) -> output form should work.
