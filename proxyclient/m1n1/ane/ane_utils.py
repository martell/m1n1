# SPDX-License-Identifier: MIT

import struct

def zero_pad(buf, size):
    if (len(buf) > size):
        raise ValueError('buf size > padded to size')
    if (len(buf) == size):
        return buf
    diff = size - len(buf)
    assert(not diff & 1)
    return buf + (struct.pack('<H', 0))*(diff//2)

def chunks(xs, size):
    # https://stackoverflow.com/a/312464
    n = max(1, size)
    return list((xs[i:i+n] for i in range(0, len(xs), n)))

def nextpow2(v):
    # https://stackoverflow.com/a/466242
    v -= 1
    v |= v >> 1
    v |= v >> 2
    v |= v >> 4
    v |= v >> 8
    v |= v >> 16
    v += 1
    return v

def lz_unpack(data):
    assert((isinstance(data, bytes)) and (len(data)%4 == 0))
    return struct.unpack('<' + 'L'*(len(data)//4), data)

def lz_pack(data):
    assert((isinstance(data, tuple)) or (isinstance(data, list)))
    return struct.pack('<' + 'L'*(len(data)), *data)

