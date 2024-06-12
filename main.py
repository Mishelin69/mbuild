from typing import Any, List, Tuple
import sys
import os

from header_file import HeaderFile
from source_file import SourceFile
from file_descriptor import FileDescriptor

ALLOWED_SOURCE_EXTENSIONS: List[str] = [
    'c', 'cpp', 'cxx'
]

ALLOWED_HEADER_EXTENSIONS: List[str] = [
    'h', 'hpp', 'hxx'
]

type MBUILD_CONFIG_DICTIONARY = dict[str, Any]

MBUILD_CONFIG: MBUILD_CONFIG_DICTIONARY  = {
    "mb_header_fastecheck": True,
    "mb_dir_read_recursive": True
}

class LStrIntPair:

    def __init__(self, l: List[str], x: int) -> None:
        self.l = l
        self.x = x

def read_all_current(paths: List[str], recursive: bool) -> List[HeaderFile]:

    headers_desc: List[HeaderFile] = []
    file_good_extension: List[str] = []

    #This should take all paths given and any subdirs and find 
    #file with preset extension (ALLOWED_HEADER_EXTIONS) 
    #will be modifiable in the future
    #TL;DR: filter header files from given directories and their subdirs (if set to true)
    #this is just a weird implementation of a "stack" I guess now thinking about it
    for p in paths:

        if not os.path.isdir(p):
            print(f'PATH NOT A DIRECTORY!!\n{p}')

        p_stack: List[LStrIntPair] = []
        p_stack.append(LStrIntPair(os.listdir(p), 0))
        p_index: int = 0
        s_index: int = 0

        while len(p_stack) >= 1:

            #if we reach end of path branch move back up (pop)
            if s_index == len(p_stack[p_index].l):
                p_index -= 1
                s_index = p_stack[p_index].x
                p_stack.pop()

            p_layer: LStrIntPair = p_stack[p_index]
            _path: str = p_layer.l[s_index]

            #index into paths (push)
            if recursive and os.path.isdir(_path):
                p_stack.append(LStrIntPair(os.listdir(_path), 0))
                p_layer.x += 1
                s_index = 0
                p_index += 1

                continue

            else:
                if _path.endswith(ALLOWED_HEADER_EXTENSIONS):
                    file_good_extension.append(_path)

            s_index += 1
            p_layer.x = s_index

    #build current header file fds and
    #search for edges with their positions/read from previous and search from that
    #method/condition for search in config !!!

    return headers_desc


def read_all_indexed_last() -> List[HeaderFile]:

    index_file_path_root: str = os.path.abspath("./")

    if not os.path.isfile(index_file_path_root + "index.mbuild"):

        #skip since theyre's nothing to read and write at the end of program
        return []

    #read the file and init
    headers: List[HeaderFile] = []

    with open(index_file_path_root + "index.mbuild", "rb") as f:

        n_entries_bdat: bytes = f.readline()
        n_entries: int = HeaderFile.read_next_int(n_entries_bdat)[0]

        for _ in range(n_entries):
            headers.append(HeaderFile.create_from_file_handle(f))

    return headers

def main() -> int:

    DESTINATION_DIRS: List[str] = []

    if len(sys.argv) > 2:

        for x in sys.argv[1:]:

            if not os.path.isdir(x):
                print("PATH NOT A DIR !!! " + x)
                exit(-1)

            DESTINATION_DIRS.append(os.path.abspath(x))

    else:
       DESTINATION_DIRS.append(os.path.abspath("./test_dir/")) 

    reader_list: List[HeaderFile] = read_all_indexed_last()

    print(reader_list[0])

    return 0

if __name__ == '__main__':
    main()
