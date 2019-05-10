from struct import unpack


class RTPDatagram:
    '''
    RTP protocol datagram parser
    Based on github.com/plazmer/pyrtsp with minor cosmetic changes
    '''

    def __init__(self, datagram):
        self.version = 0
        self.padding = 0
        self.extension = 0
        self.csrc_count = 0
        self.marker = 0
        self.payload_type = 0
        self.sequence_number = 0
        self.timestamp = 0
        self.sync_source_id = 0
        self.csrs = []
        self.extension_header = b''
        self.extension_header_id = 0
        self.extension_header_len = 0
        self.payload = b''
        self.datagram = datagram

    @property
    def datagram(self):
        return self.__datagram

    @datagram.setter
    def datagram(self, data):
        ver_p_x_cc, m_pt, self.sequence_number, self.timestamp, self.sync_source_id = unpack('!BBHII', data[:12])
        self.version =     (ver_p_x_cc & 0b11000000) >> 6
        self.padding =     (ver_p_x_cc & 0b00100000) >> 5
        self.extension =   (ver_p_x_cc & 0b00010000) >> 4
        self.csrc_count =   ver_p_x_cc & 0b00001111
        self.marker =      (m_pt & 0b10000000) >> 7
        self.payload_type = m_pt & 0b01111111

        i = 0
        for i in range(0, self.csrc_count, 4):
            self.csrc.append(unpack('!I', d[12+i:16+i]))

        if self.extension:
            i = self.csrc_count * 4
            (self.extension_header_id, self.extension_header_len) = unpack('!HH', data[12+i:16+i])
            self.extension_header = d[16+i:16+i+self.extension_header_len]
            i += 4 + self.extension_header_length

        self.payload = data[12+i:]
        self.__datagram = data
