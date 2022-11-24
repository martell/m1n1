# SPDX-License-Identifier: MIT

import struct
import numpy as np

from m1n1.ane.ane_utils import * 


class ANETiler:

    U_w = 0x40 # work unit width
    step = 2**-2
    precision = int(1/step)

    def __init__(self, xcount=1000):
        self.xdata = np.arange(0, xcount)
        self.yV_arr = self.f_transform()

    def f2_transform(self, x):
        x += 2
        if not (is_pow2(x)): return 0
        return -(2 << (9 - pow2log2(x)))

    def f_transform(self):
        delta2 = np.array([self.f2_transform(x) for x in self.xdata])
        delta = np.array([0] + list(np.cumsum(delta2))) + 0x400
        ydata = np.array([0] + list(np.cumsum(delta))) + 0x3400
        return ydata

    def xV_2_yV(self, xV):
        yV = self.yV_arr[int(xV*4) - 1]
        assert(yV == yV & 0xffff)
        return yV

    def yV_2_xV(self, yV):
        if (yV == 0): return 0
        return (np.where(self.yV_arr == yV)[0][0] / 4) + self.step
    
    def tile2arr1d(self, tile, dim):
        assert(len(dim) == 1)
        yVs = struct.unpack('<' + 'H'*(len(tile)//2), tile)[:dim[0]]
        out_arr = np.array([self.yV_2_xV(yV) for yV in yVs])
        return out_arr

    def tile2arr(self, tile, dim):
        assert(len(dim) == 4)
        (N, C, H, W) = dim
        yV_c = W # unk
        U_c = C * H # definite
        assert(yV_c <= self.U_w)

        unpacked = struct.unpack('<' + 'H'*(len(tile)//2), tile)
        units = chunks(unpacked, self.U_w//2)[:U_c]

        out_arr = []
        for unit in units:
            row = []
            for yV in unit[:yV_c]:
                row.append(self.yV_2_xV(yV))
            out_arr.append(row)
        out_arr = np.array(out_arr)
        out_arr = out_arr.reshape((N, C, H, W))
        return out_arr
    
    def arr1d2tile(self, in_arr):
        assert(in_arr.ndim == 1)
        yVs = [struct.pack('<H', self.xV_2_yV(xV)) for xV in in_arr]
        tile = b''.join(yVs)
        tile = zero_pad(tile, nxtmult4(len(tile)))
        return tile

    def arr2tile(self, in_arr):
        assert(in_arr.ndim == 4)
        N, C, H, W = in_arr.shape
        collapsed = in_arr.reshape((C*H, W))
        yV_c = W
        units = []
        for unit_slice in collapsed:
            yVs = []
            for xV in unit_slice:
                yVs.append(self.xV_2_yV(xV))
            unit = struct.pack('<' + 'H'*yV_c, *yVs)
            unit = zero_pad(unit, self.U_w)
            units.append(unit)
        tile = b''.join(units)
        return tile

    def arr2krn(self, in_arr):
        # krn swizz/tiling is slighly different
        # should never need to un-tile kernel though
        assert(in_arr.ndim == 4)
        N, C, H, W = in_arr.shape
        collapsed = in_arr.reshape((H, C*W))
        yV_c = C # definite
        U_c = H * W # unk
        assert(yV_c <= self.U_w)

        units = []
        for unit_slice in collapsed:
            yVs = []
            for xV in unit_slice:
                yVs.append(self.xV_2_yV(xV))
            unit = struct.pack('<' + 'H'*yV_c, *yVs)
            unit = zero_pad(unit, self.U_w)
            units.append(unit)
        krn = b''.join(units)
        return krn
