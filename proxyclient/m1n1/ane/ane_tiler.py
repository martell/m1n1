# SPDX-License-Identifier: MIT

import struct
import numpy as np
from m1n1.ane.ane_utils import * 


class ANETiler:

    U_w = 0x40 # work unit width

    def arr2tile(self, in_arr):
        if (in_arr.ndim == 1): # no work unit for 1D
            tile = b''.join([half2bytes(x) for x in in_arr])
            tile = zero_pad(tile, nxtmult4(len(tile)))
            return tile

        elif (in_arr.ndim == 2):
            tile = []
            for unit_slice in in_arr:
                unit = b''.join([half2bytes(x) for x in unit_slice])
                unit = zero_pad(unit, self.U_w)
                tile.append(unit)
            tile = b''.join(tile)
            return tile
        
        elif (in_arr.ndim == 3):
            tile = []
            for block in in_arr: # collapse 0 w/ 1 to make units
                for unit_slice in block:
                    unit = b''.join([half2bytes(x) for x in unit_slice])
                    unit = zero_pad(unit, self.U_w)
                    tile.append(unit)
            tile = b''.join(tile)
            return tile
        
        elif (in_arr.ndim == 4):
            tile = []
            for batch in in_arr:
                for chan in batch: 
                    units = [] # collapse 0,1,2 to make units
                    for height in chan: # unit_slice
                        units.append(b''.join([half2bytes(x) for x in height]))
                    units = [zero_pad(unit, self.U_w) for unit in units]
                    units = b''.join(units)
                    tile.append(units)
            tile = b''.join(tile)
            return tile
        
        else:
            raise ValueError ('invalid arr dimensions')
        return tile


    def tile2arr(self, tile, dim):
        if (len(dim) == 1):
            coded = struct.unpack('<' + 'h'*(len(tile)//2), tile)[:dim[-1]]
            out_arr = np.array([decodehalf(x) for x in coded])
            return out_arr

        if (len(dim) == 2):
            out_arr = []
            for unit_c in range(dim[0]):
                unit = tile[unit_c*self.U_w:(unit_c+1)*self.U_w]
                coded = struct.unpack('<' + 'h'*(len(unit)//2), unit)[:dim[-1]]
                out_arr.append([decodehalf(x) for x in coded])
            out_arr = np.array(out_arr)
            return out_arr

        if (len(dim) == 3):
            out_arr = []
            for unit_c in range(dim[0]*dim[1]):
                unit = tile[unit_c*self.U_w:(unit_c+1)*self.U_w]
                coded = struct.unpack('<' + 'h'*(len(unit)//2), unit)[:dim[-1]]
                out_arr.append([decodehalf(x) for x in coded])
            out_arr = np.array(out_arr)
            out_arr = out_arr.reshape(dim)
            return out_arr

        if (len(dim) == 4):
            out_arr = []
            for unit_c in range(dim[0]*dim[1]*dim[2]):
                unit = tile[unit_c*self.U_w:(unit_c+1)*self.U_w]
                coded = struct.unpack('<' + 'h'*(len(unit)//2), unit)[:dim[-1]]
                out_arr.append([decodehalf(x) for x in coded])
            out_arr = np.array(out_arr)
            out_arr = out_arr.reshape(dim)
            return out_arr
        
        else:
            raise ValueError ('invalid arr dimensions')
        return out_arr
    

    def arr2krn(self, in_arr):
        # TODO
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
            unit = b''.join([half2bytes(x) for x in unit_slice])
            unit = zero_pad(unit, self.U_w)
            units.append(unit)
        krn = b''.join(units)
        return krn
