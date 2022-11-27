# SPDX-License-Identifier: MIT

import numpy as np
from m1n1.ane.ane_utils import ez_pack

def compile_matmul2d(x, y):
    """
    matrix multiplication
    A @ B = C
    A: (M, N)
    B: (N, P)
    C: (M, P)

    params:
    M = 5 # HOLD
    1 <= N <= 1024
    1 <= P <= 16
    """
    base = np.load('m1n1/ane/compiler/matmul2d_base.npy')
    for key in transform_map:
        base[key//4] = transform_map[key](x, y)
    base = list(base)
    return ez_pack(base)

transform_map = {
    0x128: lambda x, y: 0x10000 | x,
    0x13c: lambda x, y: 0x10000 | x,
    0x15c: lambda x, y: func_0x15c(x),
    
    0x17c: lambda x, y: (((x-1)//0x20)+1)*0x40,
    0x178: lambda x, y: (((x-1)//0x20)+1)*0x40*5,
    0x180: lambda x, y: (((x-1)//0x20)+1)*0x40*5,
    0x184: lambda x, y: (((x-1)//0x20)+1)*0x40*5,
    
    0x1ec: lambda x, y: min((((x-1)//0x8)+1)*0x10, 0x100),
    0x1f0: lambda x, y: min((((x-1)//0x8)+1)*0x10*5, 0x100*5),
    0x1f4: lambda x, y: min((((x-1)//0x8)+1)*0x10*5, 0x100*5),
    0x1f8: lambda x, y: min((((x-1)//0x8)+1)*0x10*5, 0x100*5),
    0x214: lambda x, y: min((((x-1)//0x8)+1)*0x10*5, 0x100*5),

    0x260: lambda x, y: (((x-1)//0x20)+1)*0x40,
    0x264: lambda x, y: (((x-1)//0x20)+1)*0x40,
    0x268: lambda x, y: (((x-1)//0x20)+1)*0x40*5,
    0x26c: lambda x, y: (((x-1)//0x20)+1)*0x40*5,

    0x304: lambda x, y: 0x9d0000 | int(x >= 0x216),

    0x428: lambda x, y: 0x10000 * x | y,
    0x43c: lambda x, y: 0x10000 * x | y,
    0x450: lambda x, y: x,
    0x45c: lambda x, y: 0x4011101,

    0x478: lambda x, y: (((y-1)//0x20)+1)*0x40,
    0x47c: lambda x, y: (((y-1)//0x20)+1)*(x * 0x40),
    0x480: lambda x, y: (((y-1)//0x20)+1)*(x * 0x40),
    0x484: lambda x, y: (((y-1)//0x20)+1)*(x * 0x40),
    
    0x4e8: lambda x, y: (((y-1)//8) + 1)*0x10*x,
    0x4f0: lambda x, y: 0x20,

    0x4f4: lambda x, y: min((((y-1)//8)+1)*0x10, 0x80),
    0x4f8: lambda x, y: min((((y-1)//8)+1)*0x10, 0x80),
    0x4ec: lambda x, y: min((((y-1)//8)+1)*0x10, 0x80),
    0x514: lambda x, y: func_0x514(x, y),
    0x518: lambda x, y: (((y-1)//8)+1)*0x10,
    0x51c: lambda x, y: (((y-1)//8)+1)*0x10,
    0x520: lambda x, y: (((y-1)//8)+1)*0x10,
    
    0x67c: lambda x, y: (((x-1)//0x20)+1)*0x40,
    0x680: lambda x, y: (((x-1)//0x20)+1)*0x80,
    0x684: lambda x, y: (((x-1)//0x20)+1)*0xc0,

    0x6b8: lambda x, y: (((x-1)//0x20)+1)*0x40,
    0x6bc: lambda x, y: (((x-1)//0x20)+1)*0x40,
    0x6c0: lambda x, y: (((x-1)//0x20)+1)*0x40,
    0x6c4: lambda x, y: (((x-1)//0x20)+1)*0x40,
    
    0x72c: lambda x, y: 0x10000 | y,
    0x738: lambda x, y: x,
    0x740: lambda x, y: 0x10000 | y,
    0x7e8: lambda x, y: func_0x7e8(x),
    0x7ec: lambda x, y: func_0x7ec(x, y),
    0x7f0: lambda x, y: (((y-1)//8)+1)*0x10,
    0x7f4: lambda x, y: (((y-1)//0x8)+1)*0x10,
    0x7f8: lambda x, y: (((y-1)//0x8)+1)*0x10,

    0x818: lambda x, y: (((y-1)//8)+1)*0x10*x,
    0x81c: lambda x, y: (((y-1)//0x8)+1)*0x10,
    0x820: lambda x, y: (((y-1)//0x8)+1)*0x10*5,
    0x824: lambda x, y: (((y-1)//0x8)+1)*0x10*5,
    
    0x978: lambda x, y: (((x-1)//0x20)+1)*0x100,
    0x9b8: lambda x, y: (((x-1)//0x20)+1)*0x40,
    
    0xa2c: lambda x, y: 0x10000 | y,
    0xa38: lambda x, y: x,
    0xa40: lambda x, y: 0x10000 | y,
    
    0xaec: lambda x, y: func_0xaec(x, y),

    0xaf0: lambda x, y: (((y-1)//8)+1)*0x10,
    0xaf4: lambda x, y: (((y-1)//8) + 1)*0x10,
    0xaf8: lambda x, y: (((y-1)//8) + 1)*0x10,
    0xb18: lambda x, y: (((y-1)//8)+1)*(0x40+(x*0x10)),
    0xb1c: lambda x, y: (((y-1)//8) + 1)*0x10,
    0xb20: lambda x, y: (((y-1)//8) + 1)*0x10*5,
    0xb24: lambda x, y: (((y-1)//8) + 1)*0x10*5,

    0xd28: lambda x, y: (0x10000 * 5) | y,
    0xd3c: lambda x, y: (0x10000 * 5) | y,
    0xd5c: lambda x, y: func_0xd5c(y),

    0xde8: lambda x, y: (((y-1)//8)+1)*0x10*x,
    0xdec: lambda x, y: (((y-1)//8) + 1)*0x10*5,
    0xdf0: lambda x, y: (((y-1)//8) + 1)*0x10,
    0xdf4: lambda x, y: (((y-1)//8) + 1)*0x10*5,

    0xe14: lambda x, y: (((y-1)//8)+1)*(0x50+(x*0x10)),
    0xe60: lambda x, y: (((y-1)//0x20) + 1)*0x40,
    0xe64: lambda x, y: (((y-1)//0x20) + 1)*0x40*5,
    0xe68: lambda x, y: (((y-1)//0x20) + 1)*0x40*5,
    0xe6c: lambda x, y: (((y-1)//0x20) + 1)*0x40*5,
}

def func_0x15c(x):
    if (1 <= x <= 0x40): return 0x4191101
    return 0x4190101

def func_0x514(x, y):
    if (1 <= x <= 3): return 0x50 * (((y-1)//8) + 1)
    return 0x0

def func_0x7e8(x):
    if (x == 1): return 0x104
    return 0x120

def func_0x7ec(x, y):
    if (1 <= x <= 3): return 0x50 * (((y-1)//8) + 1)
    return 0

def func_0xaec(x, y):
    if (1 <= x <= 3): return 0x50 * (((y-1)//8) + 1)
    return 0

def func_0xd5c(y):
    if (((y-1)//0x20) & 1): return 0x4011101
    return 0x4021101

