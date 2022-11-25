# SPDX-License-Identifier: MIT

import numpy as np
from m1n1.ane.ane_utils import ez_pack

def compile_matmul2d(x):
    base = np.load('m1n1/ane/compiler/matmul2d_base.npy')
    for key in transform_map:
        base[key//4] = transform_map[key](x)
    base = list(base)
    return ez_pack(base)

transform_map = {
    
    0x128: lambda x: 0x10000 | x,
    0x13c: lambda x: 0x10000 | x,
    0x15c: lambda x: func_0x15c(x),
    
    0x17c: lambda x: ((x-1)//0x20)*0x40 + 0x40,
    0x178: lambda x: ((x-1)//0x20)*0x140 + 0x140,
    0x180: lambda x: ((x-1)//0x20)*0x140 + 0x140,
    0x184: lambda x: ((x-1)//0x20)*0x140 + 0x140,
    
    0x1ec: lambda x: min(((x-1)//0x8)*0x10 + 0x10, 0x100),
    0x1f0: lambda x: min(((x-1)//0x8)*0x10*5 + 0x10*5, 0x100*5),
    0x1f4: lambda x: min(((x-1)//0x8)*0x10*5 + 0x10*5, 0x100*5),
    0x1f8: lambda x: min(((x-1)//0x8)*0x10*5 + 0x10*5, 0x100*5),

    0x214: lambda x: min((5*0x10)*((x-1)//8) + (5*0x10), 5*0x100),
    0x260: lambda x: ((x-1)//0x20)*0x40 + 0x40,
    0x264: lambda x: ((x-1)//0x20)*0x40 + 0x40,
    0x268: lambda x: ((x-1)//0x20)*0x140 + 0x140,
    0x26c: lambda x: ((x-1)//0x20)*0x140 + 0x140,

    0x428: lambda x: 0x10000 * x | 3,
    0x43c: lambda x: 0x10000 * x | 3,
    0x450: lambda x: x,
    
    0x45c: lambda x: func_0x45c(x),
    0x47c: lambda x: x * 0x40,
    0x480: lambda x: x * 0x40,
    0x484: lambda x: x * 0x40,
    
    0x4e8: lambda x: func_0x4e8(x),
    0x4f0: lambda x: func_0x4f0(x),
    0x514: lambda x: func_0x514(x),
    0x51c: lambda x: func_0x51c(x),
    
    0x67c: lambda x: (((x-1)//0x20)+1)*0x40,
    0x680: lambda x: (((x-1)//0x20)+1)*0x80,
    0x684: lambda x: (((x-1)//0x20)+1)*0xc0,
    0x6b8: lambda x: (((x-1)//0x20)+1)*0x40,
    0x6bc: lambda x: (((x-1)//0x20)+1)*0x40,
    0x6c0: lambda x: (((x-1)//0x20)+1)*0x40,
    0x6c4: lambda x: (((x-1)//0x20)+1)*0x40,
    
    0x738: lambda x: x,
    0x7e8: lambda x: func_0x7e8(x),
    0x7ec: lambda x: func_0x7ec(x),
    0x7f0: lambda x: func_0x7f0(x),
    0x818: lambda x: func_0x818(x),
    
    0x978: lambda x: (((x-1)//0x20)+1)*0x100,
    0x9b8: lambda x: (((x-1)//0x20)+1)*0x40,
    0xa38: lambda x: x,
    0xaec: lambda x: func_0xaec(x),
    0xaf0: lambda x: func_0xaf0(x),
    0xb18: lambda x: func_0xb18(x),
    0xde8: lambda x: func_0xde8(x),
    0xe14: lambda x: func_0xe14(x),

}

def func_0x45c(x):
    if (x <= 3): return 0x4011101
    if (4 <= x <= 7): return 0x4021101
    if (8 <= x <= 0xf): return 0x4031101
    return 0x4041101

def func_0x4e8(x):
    if (x == 1): return 0x60
    if (x == 2): return 0xd0
    if (x == 3): return 0xb0
    if (x == 4): return 0x80
    return x * 0x10 

def func_0x4f0(x):
    if (1 <= x <= 3): return 0x10
    if (4 <= x <= 7): return 0x50
    if (4 <= x <= 0xf): return 0x30
    return 0x20

def func_0x514(x):
    if (1 <= x <= 3): return 0x50
    return 0x0

def func_0x51c(x):
    if (x == 1): return 0x10
    if (x == 2): return 0x40
    if (x == 3): return 0x20
    if (x == 4): return 0x20
    return 0x10

def func_0x7e8(x):
    if (x == 1): return 0x104
    return 0x120

def func_0x7ec(x):
    if (1 <= x <= 3): return 0x50
    return 0

def func_0x7f0(x):
    if (x == 1): return 0x10
    if (x == 2): return 0x40
    if (x == 3): return 0x20
    if (x == 4): return 0x20
    return 0x10

def func_0x818(x):
    if (x == 1): return 0
    if (x == 2): return 0
    if (x == 3): return 0
    if (x == 4): return 0x80
    return 0x10*x

def func_0x7f0(x):
    if (x == 1): return 0x10
    if (x == 2): return 0x40
    if (x == 3): return 0x20
    if (x == 4): return 0x20
    return 0x10

def func_0xaec(x):
    if (1 <= x <= 3): return 0x50
    return 0

def func_0xaf0(x):
    if (x == 1): return 0x10
    if (x == 2): return 0x40
    if (x == 3): return 0x20
    if (x == 4): return 0x20
    return 0x10

def func_0xb18(x):
    if (1 <= x <= 3): return 0x40
    if (x == 4): return 0xc0
    return (x*0x10) + 0x40

def func_0xde8(x):
    if (1 <= x <= 3): return 0
    if (x == 4): return 0x80
    return (x*0x10)

def func_0xe14(x):
    if (1 <= x <= 3): return 5 * 0x10
    if (x == 4): return 0xd0
    return (x*0x10) + (5 * 0x10)

def func_0x15c(x):
    if (1 <= x <= 0x40): return 0x4191101
    return 0x4190101
