from struct import unpack


class NalUnitError(Exception):
    '''
    Raised when NAL unit contains bit error
    '''
    pass


class NalUnit:
    '''
    Network Abstraction Layer units parser
    '''

    STARTBYTES = b'\x00\x00\x00\x01'

    def __init__(self, unit, is_fragment=False):
        self.header = self.STARTBYTES
        self.forbidden = 0
        self.ref_idc = 0
        self.type = 0
        self.fragment_start = 0
        self.fragment_end = 0
        self.fragment_reserved = 0
        self.payload = b''
        self.unit = unit

    @property
    def unit(self):
        return self.__unit

    @unit.setter
    def unit(self, data):
        f_nri_type = unpack('!B',data[:1])[0]
        payload_offset = 0

        self.forbidden = (f_nri_type & 0b10000000) >> 7
        if self.forbidden:
            raise NalUnitError(
                'NAL unit type octet or payload contains bit errors')

        self.ref_idc = (f_nri_type & 0b01100000) >> 5
        self.type =     f_nri_type & 0b00011111

        if self.type == 28:
            st_end_res_nlu = unpack('!B',data[1:2])[0]
            payload_offset = 2

            self.fragment_start =    (st_end_res_nlu & 0b10000000) >> 7
            self.fragment_end =      (st_end_res_nlu & 0b01000000) >> 6
            self.fragment_reserved = (st_end_res_nlu & 0b00100000) >> 5

            if self.fragment_start:
                self.header += bytes(((f_nri_type & 0b11100000) + (st_end_res_nlu & 0b00011111),))
            else:
                self.header = b''
        elif self.type == 29:
            raise NalUnitError(
                'Defragmentation of FU-B unit type is not implemented')

        self.payload = self.header + data[payload_offset:]
        self.__unit = data
