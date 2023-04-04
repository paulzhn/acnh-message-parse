import pathlib
from enum import Enum
from typing import List

from binary_reader import BinaryReader, Endian, Whence


class ByteOrder(Enum):
    LittleEndian = 0
    BigEndian = 1


class EncodingByte(Enum):
    UTF8 = 0x00
    Unicode = 0x01


class Section:

    def __init__(self):
        self.identifier = ''
    # uint32
        self.section_size = 0
    # byte[]
        self.padding1 = []


class Group:
    def __init__(self):
        self.number_of_labels = 0
        self.offset = 0


class IEntry(object):
    value: bytearray
    index: int

    def to_string(self):
        pass

    def to_string(self, encoding):
        pass

    @property
    def value(self):
        pass

    @value.setter
    def value(self, val):
        pass

    @property
    def index(self):
        pass

    @index.setter
    def index(self, val):
        pass


class String(IEntry):
    _text: bytearray
    _index: int

    @property
    def value(self):
        return self._text

    @value.setter
    def value(self, value):
        self._text = value


class Label(IEntry):
    _index: int

    length: int
    name: str
    checksum: int
    string: String

    @property
    def value(self):
        return self.string.value

    @value.setter
    def value(self, value):
        self.string.value = value

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, value):
        self._index = value

    # def to_string(self):
    #     return (length > 0 ? name : (_index + 1).to_string())

    # def to_string(self, encoding):
    #     return (length > 0 ? name : (_index + 1).to_string())


class LBL1(Section):
    groups: List[Group]
    labels: List[Label]

    def __init__(self):
        # uint32
        self.number_of_groups = 0
        self.groups = []
        self.labels = []


class TXT2(Section):
    number_of_strings: int
    strings: List[String]
    original_strings: List[String]

    def __init__(self):
        self.number_of_strings = None
        self.strings = None
        self.original_strings = None


class ATR1(Section):
    number_of_attributes: int
    unknown2: bytearray()

    def __init__(self):
        self.number_of_attributes = 0
        self.unknown2 = []


class Msbt:
    class Header:
        def __init__(self):
            # MsgStdBn
            self.identifier = ''
            self.byte_order_mark = ''
            # uint16 Always 0x0000
            self.unknown1 = 0
            self.encoding_byte = None
            # byte Always 0x03
            self.unknown2 = 0
            # uint16
            self.number_of_sections = 0
            # uint16 Always 0x0000
            self.unknown3 = 0
            # uint32
            self.file_size = 0
            # byte[] Always 0x0000 0000 0000 0000 0000
            self.unknown4 = []
            # uint32
            self.file_size_offset = 0

    file: pathlib.Path
    lbl1: LBL1
    txt2: TXT2
    atr1: ATR1
    header: Header
    has_labels: bool
    endian: bool

    def __init__(self, filename):
        self.file = pathlib.Path(filename)
        self.lbl1 = LBL1()
        self.txt2 = TXT2()
        self.header = Msbt.Header()
        self.has_labels = False
        if self.file.exists() and len(filename) > 0:
            with open(self.file, "rb") as fs:
                br = BinaryReader(fs.read())
            # Initialize Members
            self.lbl1.groups = list()
            self.lbl1.labels = list()
            self.txt2.strings = list()
            self.txt2.original_strings = list()

            # Header
            self.header.identifier = br.read_str(8)
            if self.header.identifier != "MsgStdBn":
                raise Exception(
                    "The file provided is not a valid MSBT file.")

            # Byte Order
            self.header.byte_order_mark = br.read_bytes(2)
            br.set_endian(self.header.byte_order_mark[
                0] > self.header.byte_order_mark[1])
            self.endian = self.header.byte_order_mark[
                0] > self.header.byte_order_mark[1]

            self.header.unknown1 = br.read_uint16()

            # Encoding
            self.header.encoding_byte = EncodingByte(br.read_bytes())
            # self.file_encoding = Encoding.UTF8 if self.header.encoding_byte == EncodingByte.UTF8 else Encoding.Unicode

            self.header.unknown2 = br.read_bytes()
            self.header.number_of_sections = br.read_uint16()
            self.header.unknown3 = br.read_uint16()
            # Record offset for future use
            self.header.file_size_offset = br.pos()
            self.header.file_size = br.read_uint32()
            self.header.unknown4 = br.read_bytes(10)

            if self.header.file_size != br.size():
                raise Exception(
                    "The file provided is not a valid MSBT file.")

            self.section_order = []
            for i in range(self.header.number_of_sections):
                peek_string = br.read_str(4)
                if peek_string == "LBL1":
                    self.read_lbl1(br)
                    self.section_order.append("LBL1")
                # elif peek_string == "NLI1":
                #     self.read_nli1(br)
                #     self.section_order.append("NLI1")
                # elif peek_string == "ATO1":
                #     self.read_ato1(br)
                #     self.section_order.append("ATO1")
                elif peek_string == "ATR1":
                    self.read_atr1(br)
                    self.section_order.append("ATR1")
                # elif peek_string == "TSY1":
                #     self.read_tsy1(br)
                #     self.section_order.append("TSY1")
                elif peek_string == "TXT2":
                    self.read_txt2(br)
                    self.section_order.append("TXT2")

    def padding_seek(br: BinaryReader):
        remainder = br.pos() % 16
        if remainder > 0:
            paddingChar = br.read_bytes()
            br.seek(-1, Whence.CUR)
            br.seek(16 - remainder, Whence.CUR)

    def read_lbl1(self, br: BinaryReader):
        self.lbl1.identifier = br.read_str(4)
        self.lbl1.section_size = br.read_uint32()
        self.lbl1.padding1 = br.read_bytes(8)
        start_of_labels = br.pos()
        self.lbl1.number_of_groups = br.read_uint32()

        for i in range(self.lbl1.number_of_groups):
            grp = Group()
            grp.number_of_labels = br.read_uint32()
            grp.offset = br.read_uint32()
            self.lbl1.groups.append(grp)

        for grp in self.lbl1.groups:
            br.seek(start_of_labels + grp.offset, Whence.BEGIN)

            for i in range(grp.number_of_labels):
                lbl = Label()
                lbl.length = int.from_bytes(br.read_bytes())
                lbl.name = br.read_str(lbl.length)
                lbl.index = br.read_uint32()
                lbl.checksum = self.lbl1.groups.index(grp)
                self.lbl1.labels.append(lbl)

        # Old rename correction
        for lbl in self.lbl1.labels:
            previous_checksum = lbl.checksum
            lbl.checksum = self.label_checksum(lbl.name)

            if previous_checksum != lbl.checksum:
                self.lbl1.groups[previous_checksum].number_of_labels -= 1
                self.lbl1.groups[lbl.checksum].number_of_labels += 1

        if len(self.lbl1.labels) > 0:
            self.has_labels = True

        self.padding_seek(br)

    def read_txt2(self, br: BinaryReader):
        self.txt2.identifier = br.read_str(4)
        self.txt2.section_size = br.read_uint32()
        self.txt2.padding1 = br.read_bytes(8)
        start_of_strings = br.pos()
        self.txt2.number_of_strings = br.read_uint32()

        offsets = [0] * self.txt2.number_of_strings
        for i in range(0, self.txt2.number_of_strings):
            offsets[i] = br.read_uint32()

        for i in range(0, self.txt2.number_of_strings):
            str = String()
            nextOffset = start_of_strings + \
                offsets[i + 1] if i + \
                1 < len(offsets) else start_of_strings + self.txt2.section_size
            br.seek(start_of_strings + offsets[i], Whence.BEGIN)

            result = []
            while br.pos() < nextOffset and br.pos() < self.header.file_size:
                if self.header.encoding_byte == EncodingByte.UTF8:
                    result.append(br.read_bytes())
                else:
                    unichar = br.read_bytes(2)

                    if self.endian == Endian.BIG:
                        unichar = unichar[1] + unichar[0]

                    result.append(unichar)

            str.value = result
            str.index = i

            self.txt2.original_strings.append(str)

            # Duplicate entries for editing
            estr = String()
            estr.value = str.value
            estr.index = str.index
            self.txt2.strings.append(estr)

        # Tie in LBL1 labels
        for lbl in LBL1.labels:
            lbl.string = self.txt2.strings[lbl.index]

        self.padding_seek(br)

    def label_checksum(self, label: str) -> int:
        group = 0

        for i in range(len(label)):
            group *= 0x492
            group += label[i]
            group &= 0xFFFFFFFF

        return group % self.lbl1.number_of_groups

    def read_atr1(self, br: BinaryReader):
        self.atr1.identifier = br.read_bytes(4)
        self.atr1.section_size = br.read_uint32()
        self.atr1.padding1 = br.read_bytes(8)
        self.atr1.number_of_attributes = br.read_uint32()
        # Read in the entire section at once since we don't know what it's for
        self.atr1.unknown2 = br.read_bytes(self.atr1.section_size - 4)
        self.padding_seek(br)


m = Msbt('BO_ApproachA_Always.msbt')
