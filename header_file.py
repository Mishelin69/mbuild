from __future__ import annotations
from typing import List, Tuple
from file_descriptor import FileDescriptor
import io
import struct

type NFileHandle = io.BufferedReader

class HeaderFile:

    def __init__(self, h_file: FileDescriptor, edges: List[FileDescriptor]):
        self.h_file: FileDescriptor = h_file

        #edges consist of [source descriptor, position in file]
        #if source changes and if its enabled by config 
        self.edges: List[FileDescriptor] = edges

    @classmethod
    def create_from_file_handle(cls, handle: NFileHandle) -> HeaderFile:

        #read data according to the example and correctly process it
        file_name_bdat: bytes = handle.readline()
        st_mtime_bdat: bytes = handle.read(4)
        edges_bdat: bytes = handle.readline()
        check: bytes = handle.readline()

        #yep this will not be utf-8 encoded for simplicity
        #I just like my bytes raw, yes I like it raw
        if check[0] != b"$":
            print("Invalid file format!!")

        #conver everything to a correct format
        file_name: str = HeaderFile.read_next_str(file_name_bdat)[0]
        st_mtime: float = HeaderFile.read_next_float(st_mtime_bdat)[0]
        fd: FileDescriptor = FileDescriptor.create_from_data(file_name, st_mtime)

        comma_byte: int = 44
        l: int = 0
        r: int = 0
        edges: List[FileDescriptor] = []

        #rework this 
        #format {srcname}{NULL_BYTE_TERMINATION}st_mtime:line, {nextsrc}
        #       l -- ---r     r     r+4   r+8 = l
        while edges_bdat[r] != 0:

            if edges_bdat[r] == comma_byte:

                #build str_name
                _file_name: str = HeaderFile.read_next_str(edges_bdat[l:r])[0]
                r += 1 #skip null termination byte
                st_mtime: float = HeaderFile.read_next_float(edges_bdat[r:])[0]
                r += 4 #skip 4 bytes for float

                edges.append(FileDescriptor(_file_name, st_mtime))

                l = r

            r += 1

        return cls(fd, edges)

    @staticmethod
    def read_next_str(byte_arr: bytes) -> Tuple[str, int]:

        s: str = ""
        r: int = 0

        while byte_arr[r] != 0:
            r += 1

        return (byte_arr[:r].decode('utf-8'), r)

    #assume 32 bit ints because I doubt it'll get any bigger
    #I'd be surprised if we reached number above 1000 but to make sure
    #that we cover all obscurities I'll just do it like this
    @staticmethod
    def read_next_int(byte_arr: bytes) -> Tuple[int, int]:

        num: int = struct.unpack('i', byte_arr[:4])[0]

        return (num, 4)
    @staticmethod
    def read_next_float(byte_arr: bytes) -> Tuple[float, int]:

        num: int = struct.unpack('f', byte_arr[:4])[0]

        return (num, 4)

    def __str__(self) -> str:
        return self.h_file.__str__() + '\n'.join(x.__str__() + '\n' for x in self.edges)
