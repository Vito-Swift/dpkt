# $Id: 80211NDP.py 53 2022-01-08 01:22:57Z Vito-Swift $
# -*- coding: utf-8 -*-
"""IEEE 802.11 VHT/HE Null Data Packet Sounding Protocol"""
from __future__ import print_function
from __future__ import absolute_import

import struct
from . import dpkt
from .compat import ntole

C_VHT = 0x15
C_HE = 0x1e


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
            C_HE: ('HE', None)
        }

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

        def unpack(self, buf):
            dpkt.Packet.unpack(self, buf)
            self.data = buf[self.__hdr_len__:]

    class HEMIMOControl(dpkt.Packet):
        """802.11ax MIMO Control Decoder (Report.category=0x1e)"""
        # TODO: to implement
