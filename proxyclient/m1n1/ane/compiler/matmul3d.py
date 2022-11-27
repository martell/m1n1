# SPDX-License-Identifier: MIT

import numpy as np
from m1n1.ane.ane_utils import ez_pack

def compile_matmul3d(x, y):
    """
    matrix multiplication
    A @ B = C
    A: (M, M, N)
    B: (M, N, P)
    C: (M, P)

    params:
    M = 5 # HOLD
    N = 7 # HOLD
    1 <= P <= 50
    """
    base = np.load('m1n1/ane/compiler/matmul3d_base.npy')
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
    0x180: lambda x, y: (((x-1)//0x20)+1)*0x40*5*5,
    0x184: lambda x, y: (((x-1)//0x20)+1)*0x40*5*5,
    
    0x1ec: lambda x, y: min((((x-1)//0x8)+1)*0x10, 0x100),
    0x1f0: lambda x, y: min((((x-1)//0x8)+1)*0x10*5, 0x100*5),
    0x1f4: lambda x, y: min((((x-1)//0x8)+1)*0x10*5, 0x100*5),
    0x1f8: lambda x, y: min((((x-1)//0x8)+1)*0x10*5, 0x100*5),
    0x214: lambda x, y: min((((x-1)//0x8)+1)*0x10*5, 0x100*5),

    0x260: lambda x, y: (((x-1)//0x20)+1)*0x40,
    0x264: lambda x, y: (((x-1)//0x20)+1)*0x40,
    0x268: lambda x, y: (((x-1)//0x20)+1)*0x40*5,
    0x26c: lambda x, y: (((x-1)//0x20)+1)*0x40*5,

    0x304: lambda x, y: 0x9d0000 | int(y >= 481),

    0x428: lambda x, y: 0x10000 * x | y,
    0x43c: lambda x, y: 0x10000 * x | y,
    0x450: lambda x, y: x,
    0x45c: lambda x, y: func_0x45c(x, y),

    0x478: lambda x, y: (((y-1)//0x20)+1)*0x40,
    0x47c: lambda x, y: (((y-1)//0x20)+1)*(x * 0x40),
    0x480: lambda x, y: (((y-1)//0x20)+1)*(x * 0x40) * 5,
    0x484: lambda x, y: (((y-1)//0x20)+1)*(x * 0x40) * 5,
    
    0x4e8: lambda x, y: (((y-1)//8) + 1)*0x230,
    0x4f0: lambda x, y: min((((y-1)//8) + 1)*0x50, 0x280),
    0x4f4: lambda x, y: min((((y-1)//8) + 1)*0x50, 0x280),
    0x4f8: lambda x, y: min((((y-1)//8) + 1)*0x50, 0x280),
    0x4ec: lambda x, y: min((((y-1)//8)+1)*0x10, 0x80),
    0x514: lambda x, y: func_0x514(x, y),
    0x518: lambda x, y: (((y-1)//8)+1)*0x10,
    0x520: lambda x, y: (((y-1)//8)+1)*0x10*5,
    0x51c: lambda x, y: (((y-1)//8) + 1)*0x10*5,
    
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
    0x7ec: lambda x, y: (((y-1)//8)+1)*0x40,
    0x7f0: lambda x, y: (((y-1)//8)+1)*0x10*5,
    0x7f4: lambda x, y: (((y-1)//0x8)+1)*0x10,
    0x7f8: lambda x, y: (((y-1)//0x8)+1)*0x10*5,
    0x818: lambda x, y: (((y-1)//0x8)+1)*0x370,
    0x81c: lambda x, y: (((y-1)//0x8)+1)*0x10,
    0x820: lambda x, y: (((y-1)//0x8)+1)*0x10*5,
    0x824: lambda x, y: (((y-1)//0x8)+1)*0x10*5,
    
    0x978: lambda x, y: (((x-1)//0x20)+1)*0x100,
    0x9b8: lambda x, y: (((x-1)//0x20)+1)*0x40,
    
    0xa2c: lambda x, y: 0x10000 | y,
    0xa38: lambda x, y: x,
    0xa40: lambda x, y: 0x10000 | y,

    0xaf4: lambda x, y: (((y-1)//8) + 1)*0x10,
    0xaf8: lambda x, y: (((y-1)//8) + 1)*0x10,

    0xaec: lambda x, y: (((y-1)//8)+1)*0x40,
    0xaf0: lambda x, y: (((y-1)//8)+1)*0x10*5,
    0xaf8: lambda x, y: (((y-1)//8)+1)*0x10*5,
    0xb18: lambda x, y: (((y-1)//8)+1)*0x3b0,
    0xb1c: lambda x, y: (((y-1)//8)+1)*0x10,
    0xb20: lambda x, y: (((y-1)//8)+1)*0x10*5,
    0xb24: lambda x, y: (((y-1)//8)+1)*0x10*5,

    0xde8: lambda x, y: (((y-1)//8) + 1)*0x3c0,
    0xe14: lambda x, y: ((((y-1)//8)+1)*0x3c0) + 0x50,

    0x102c: lambda x, y: 0x10000 | y,
    0x1040: lambda x, y: 0x10000 | y,
    0x10ec: lambda x, y: (((y-1)//8) + 1)*0x30,
    0x10f0: lambda x, y: (((y-1)//8) + 1)*0x50,
    0x10f4: lambda x, y: (((y-1)//8) + 1)*0x10,
    0x10f8: lambda x, y: (((y-1)//8) + 1)*0x10*5,
    0x1118: lambda x, y: (((y-1)//8) + 1)*0x10*0x32,
    0x111c: lambda x, y: (((y-1)//8) + 1)*0x10,
    0x1120: lambda x, y: (((y-1)//8) + 1)*0x10*5,
    0x1124: lambda x, y: (((y-1)//8) + 1)*0x10*5,

    0x132c: lambda x, y: 0x10000 | y,
    0x1340: lambda x, y: 0x10000 | y,
    0x13ec: lambda x, y: (((y-1)//8) + 1)*0x30,
    0x13f0: lambda x, y: (((y-1)//8) + 1)*0x50,
    0x13f4: lambda x, y: (((y-1)//8) + 1)*0x10,
    0x13f8: lambda x, y: (((y-1)//8) + 1)*0x10*5,
    0x1418: lambda x, y: (((y-1)//8) + 1)*0x10*0x36,
    0x141c: lambda x, y: (((y-1)//8) + 1)*0x10,
    0x1420: lambda x, y: (((y-1)//8) + 1)*0x10*5,
    0x1424: lambda x, y: (((y-1)//8) + 1)*0x10*5,

    0x16e8: lambda x, y: (((y-1)//8) + 1)*0x3c0,
    0x1714: lambda x, y: ((((y-1)//8)+1)*0x3c0) + 0x50,

    0x192c: lambda x, y: 0x10000 | y,
    0x1940: lambda x, y: 0x10000 | y,
    0x19ec: lambda x, y: (((y-1)//8) + 1)*0x20,
    0x19f0: lambda x, y: (((y-1)//8) + 1)*0x50,
    0x19f4: lambda x, y: (((y-1)//8) + 1)*0x10,
    0x19f8: lambda x, y: (((y-1)//8) + 1)*0x10*5,
    0x1a18: lambda x, y: (((y-1)//8) + 1)*0x2d0,
    0x1a1c: lambda x, y: (((y-1)//8) + 1)*0x10,
    0x1a20: lambda x, y: (((y-1)//8) + 1)*0x10*5,
    0x1a24: lambda x, y: (((y-1)//8) + 1)*0x10*5,

    0x1c2c: lambda x, y: 0x10000 | y,
    0x1c40: lambda x, y: 0x10000 | y,
    0x1cec: lambda x, y: (((y-1)//8) + 1)*0x30,
    0x1cf0: lambda x, y: (((y-1)//8) + 1)*0x50,
    0x1cf4: lambda x, y: (((y-1)//8) + 1)*0x10,
    0x1cf8: lambda x, y: (((y-1)//8) + 1)*0x10*5,

    0x1cec: lambda x, y: (((y-1)//8) + 1)*0x20,
    0x1d18: lambda x, y: (((y-1)//8) + 1)*0x310,
    0x1d1c: lambda x, y: (((y-1)//8) + 1)*0x10,
    0x1d20: lambda x, y: (((y-1)//8) + 1)*0x10*5,
    0x1d24: lambda x, y: (((y-1)//8) + 1)*0x10*5,
    0x1fe8: lambda x, y: (((y-1)//8) + 1)*0x3c0,
    0x2014: lambda x, y: (((y-1)//8) + 1)*0x3c0 + 0x50,

    0x222c: lambda x, y: 0x10000 | y,
    0x2240: lambda x, y: 0x10000 | y,
    0x22ec: lambda x, y: (((y-1)//8) + 1)*0x10,
    0x22f0: lambda x, y: (((y-1)//8) + 1)*0x50,
    0x22f4: lambda x, y: (((y-1)//8) + 1)*0x10,
    0x22f8: lambda x, y: (((y-1)//8) + 1)*0x10*5,
    0x2318: lambda x, y: (((y-1)//8) + 1)*0x280,
    0x231c: lambda x, y: (((y-1)//8) + 1)*0x10,
    0x2320: lambda x, y: (((y-1)//8) + 1)*0x10*5,
    0x2324: lambda x, y: (((y-1)//8) + 1)*0x10*5,

    0x252c: lambda x, y: 0x10000 | y,
    0x2540: lambda x, y: 0x10000 | y,
    0x25ec: lambda x, y: (((y-1)//8) + 1)*0x10,
    0x25f0: lambda x, y: (((y-1)//8) + 1)*0x50,
    0x25f4: lambda x, y: (((y-1)//8) + 1)*0x10,
    0x25f8: lambda x, y: (((y-1)//8) + 1)*0x10*5,
    0x2618: lambda x, y: (((y-1)//8) + 1)*0x2c0,
    0x261c: lambda x, y: (((y-1)//8) + 1)*0x10,
    0x2620: lambda x, y: (((y-1)//8) + 1)*0x10*5,
    0x2624: lambda x, y: (((y-1)//8) + 1)*0x10*5,
    0x28e8: lambda x, y: (((y-1)//8) + 1)*0x3c0,
    0x2914: lambda x, y: (((y-1)//8) + 1)*0x3c0 + 0x50,

    0x2b2c: lambda x, y: 0x10000 | y,
    0x2b40: lambda x, y: 0x10000 | y,
    0x2bf0: lambda x, y: (((y-1)//8) + 1)*0x50,
    0x2bf4: lambda x, y: (((y-1)//8) + 1)*0x10,
    0x2bf8: lambda x, y: (((y-1)//8) + 1)*0x10*5,
    0x2c18: lambda x, y: (((y-1)//8) + 1)*0x230,
    0x2c1c: lambda x, y: (((y-1)//8) + 1)*0x10,
    0x2c20: lambda x, y: (((y-1)//8) + 1)*0x10*5,
    0x2c24: lambda x, y: (((y-1)//8) + 1)*0x10*5,

    0x2e2c: lambda x, y: 0x10000 | y,
    0x2e40: lambda x, y: 0x10000 | y,
    0x2ef0: lambda x, y: (((y-1)//8) + 1)*0x50,
    0x2ef4: lambda x, y: (((y-1)//8) + 1)*0x10,
    0x2ef8: lambda x, y: (((y-1)//8) + 1)*0x10*5,
    0x2f18: lambda x, y: (((y-1)//8) + 1)*0x270,
    0x2f1c: lambda x, y: (((y-1)//8) + 1)*0x10,
    0x2f20: lambda x, y: (((y-1)//8) + 1)*0x10*5,
    0x2f24: lambda x, y: (((y-1)//8) + 1)*0x10*5,

    0x3128: lambda x, y: 0x50000 | y,
    0x313c: lambda x, y: 0x50000 | y,
    0x31e8: lambda x, y: (((y-1)//8) + 1)*0x230,
    0x31ec: lambda x, y: (((y-1)//8) + 1)*0x50,
    0x31f0: lambda x, y: (((y-1)//8) + 1)*0x10,
    0x31f4: lambda x, y: (((y-1)//8) + 1)*0x10*5,
    0x3214: lambda x, y: (((y-1)//8) + 1)*0x3c0,

    0x315c: lambda x, y: func_0x315c(y),
    0x3260: lambda x, y: ((y-1)//0x20 + 1) * 0x40,
    0x3264: lambda x, y: ((y-1)//0x20 + 1) * 0x140,
    0x3268: lambda x, y: ((y-1)//0x20 + 1) * 0x640,
    0x326c: lambda x, y: ((y-1)//0x20 + 1) * 0x640,
}

def func_0x15c(x):
    if (1 <= x <= 0x40): return 0x4191101
    return 0x4190101

def func_0x45c(x, y):
    if (((y-1)//0x20) & 1): return 0x4191101
    return 0x41a1101

def func_0x514(x, y):
    if (1 <= x <= 3): return 0x50 * (((y-1)//8) + 1)
    return 0x0

def func_0x7e8(x):
    if (x == 1): return 0x104
    return 0x120

def func_0x315c(y):
    if (((y-1)//0x20) & 1): return 0x4191101
    return 0x41a1101
