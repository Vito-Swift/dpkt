# $Id: 80211NDP.py 53 2022-01-08 01:22:57Z Vito-Swift $
# -*- coding: utf-8 -*-
"""IEEE 802.11 VHT/HE Null Data Packet Sounding Protocol"""
from __future__ import print_function
from __future__ import absolute_import

from . import dpkt
from .compat import ntole

C_VHT = 0x15
C_HE = 0x1e

angle_representation_table = [
    [2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # 2 x 1
    [2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # 2 x 2
    [2, 2, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0],  # 3 x 1
    [2, 2, 1, 1, 2, 1, 0, 0, 0, 0, 0, 0],  # 3 x 2
    [2, 2, 1, 1, 2, 1, 0, 0, 0, 0, 0, 0],  # 3 x 3
    [2, 2, 2, 1, 1, 1, 0, 0, 0, 0, 0, 0],  # 4 x 1
    [2, 2, 2, 1, 1, 1, 2, 2, 1, 1, 0, 0],  # 4 x 2
    [2, 2, 2, 1, 1, 1, 2, 2, 1, 1, 2, 1],  # 4 x 3
    [2, 2, 2, 1, 1, 1, 2, 2, 1, 1, 2, 1],  # 4 x 4
]
angle_psi_val = 0x1
angle_phi_val = 0x2


def signbit_convert(data, maxbit):
    if data & (1 << (maxbit - 1)):
        data -= (1 << maxbit)
    return data


class IEEE80211NDP(dpkt.Packet):
    __hdr__ = (
        ('category', 'H', 0),  # Category code, i.e. VHT=0x15
        ('action', 'H', 0)  # Action code, i.e. VHTCompressedBeamforming=0
    )

    @property
    def category(self):
        return self.category

    @property
    def action(self):
        return self.action

    def __init__(self, *args, **kwargs):
        super(IEEE80211NDP, self).__init__(*args, **kwargs)

    def unpack(self, buf):
        dpkt.Packet.unpack(self, buf)
        self.data = buf[self.__hdr_len__:]

        decoder = {
            C_VHT: ('VHT', self.VHTMIMOControl),
            C_HE: ('HE', self.HEMIMOControl),
        }
        try:
            parser = decoder[self.category][1]
            name = decoder[self.category][0]
            # todo: What's next?
        except KeyError:
            raise dpkt.UnpackError("KeyError: category=%s" % self.category)

    class VHTMIMOControl(dpkt.Packet):
        """802.11ac MIMO Control Decoder (Report.category=0x15)"""
        __hdr__ = (
            ('_vht_mimo_ctrl', '3s', b'\x00' * 3)
        )
        __bit_fields__ = {
            '_vht_mimo_ctrl': (
                ('nc', 3),  # Number of columns, 3 bits
                ('nr', 3),  # Number of rows, 3 bits
                ('bw', 2),  # Channel bandwidth, 2 bits
                ('ng', 2),  # Grouping, 2 bits
                ('codebook', 1),  # Codebook information, 1 bit
                ('fb', 1),  # Feedback type, 1 bit
                ('rm', 3),  # Remaining feedback segments, 3 bits
                ('ffs', 1),  # First feedback segment, 1 bit
                ('rs', 2),  # Reserved, 2 bits
                ('sounding_token', 6),  # Sounding dialog token number, 6 bits
            )
        }

        @property
        def nc(self):
            """Number of columns (equiv.., number of Space-Time Streams)"""
            return self.nc + 1

        @property
        def nr(self):
            """Number of rows (equiv.., number of TX antennas)"""
            return self.nr + 1

        @property
        def ns(self):
            """Number of subcarriers"""
            ns_codebook = {
                # Bandwidth
                20: {0: 52, 1: 30, 2: 16},
                40: {0: 108, 1: 58, 2: 30},
                80: {0: 234, 1: 122, 2: 62},
                160: {0: 468, 2: 244, 1: 124},
            }

            return ns_codebook[self.channel_bandwidth][self.ng]

        @property
        def channel_bandwidth(self):
            """Channel bandwidth (in MHz)"""
            bw_codebook = {
                0x0: 20,
                0x1: 40,
                0x2: 80,
                0x3: 160
            }

            return bw_codebook[self.bw]

        @property
        def phi_size(self):
            """Size of angle phi (in bits)"""
            phi_codebook = {
                # SU-MIMO
                0: {0: 4, 1: 6},
                # MU-MIMO
                1: {0: 7, 1: 9},
            }

            return phi_codebook[self.fb][self.codebook]

        @property
        def psi_size(self):
            """Size of angle psi (in bits)"""
            psi_codebook = {
                # SU-MIMO
                0: {0: 2, 1: 4},
                # MU-MIMO
                1: {0: 5, 1: 7},
            }
            return psi_codebook[self.fb][self.codebook]

        @property
        def na(self):
            """Number of angles"""
            if self.nr == 0x2:
                return 0x2
            na_codebook = {
                # nr
                0x3: {0x1: 0x4, 0x2: 0x6, 0x3: 0x6},  # nc
                0x4: {0x1: 0x6, 0x2: 0xa, 0x3: 0xc, 0x4: 0xc},  # nc
            }
            return na_codebook[self.nr][self.nc]

        def unpack(self, buf):
            dpkt.Packet.unpack(self, buf)
            self.data = buf[self.__hdr_len__:]

            # parse ASNR field
            asnr_parse = lambda ansr: -10.0 + (ansr + 128) * 0.25
            self.asnr = [asnr_parse(self.data[i]) for i in range(self.nc)]

            # parse compressed beamforming matrix
            self.angle = [[] for i in range(self.ns)]
            idx = 2
            phi_size = self.phi_size
            psi_size = self.psi_size
            phi_mask = (1 << phi_size) - 1
            psi_mask = (1 << psi_size) - 1

            # read 2 bytes (16 bits) a single time
            elem = self.data[idx]
            idx += 1
            elem += (self.data[idx] << 8)
            idx += 1

            bits_left = 16
            current_data = elem & ((1 << 16) - 1)
            angle_rp_idx = ((2 + self.nc) * (self.nc - 2) / 2) + self.nr - 1
            for k in range(self.ns):
                for angle_idx in range(self.na):
                    if angle_representation_table[angle_rp_idx][angle_idx] == angle_psi_val:
                        # parse angle psi
                        if bits_left - psi_size < 0:
                            elem = self.data[idx]
                            idx += 1
                            elem += (self.data[idx] << 8)
                            idx += 1
                            current_data += elem << bits_left
                            bits_left += 16
                        val = current_data & psi_mask
                        self.angle[k].append(signbit_convert(val, psi_size))

                        bits_left -= psi_size
                        current_data = current_data >> psi_size

                    elif angle_representation_table[angle_rp_idx][angle_idx] == angle_phi_val:
                        # parse angle phi
                        if bits_left - phi_size < 0:
                            elem = self.data[idx]
                            idx += 1
                            elem += (self.data[idx] << 8)
                            idx += 1
                            current_data += elem << bits_left
                            bits_left += 16
                        val = current_data & phi_mask
                        self.angle[k].append(signbit_convert(val, phi_size))

                        bits_left -= phi_size
                        current_data = current_data >> phi_size

    class HEMIMOControl(dpkt.Packet):
        """802.11ax MIMO Control Decoder (Report.category=0x1e)"""
        # TODO: to be implemented
