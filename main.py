from typing import Any, List
import sys
import os

from header_file import HeaderFile
from source_file import SourceFile
from file_descriptor import FileDescriptor

ALLOWED_SOURCE_EXTENSIONS: List[str] = [
    'c', 'cpp', 'cxx'
]

ALLOWED_HEADER_EXTENSIONS: List[str] = [
    'c', 'cpp', 'cxx'
]

type MBUILD_CONFIG_DICTIONARY = dict[str, Any]

MBUILD_CONFIG: MBUILD_CONFIG_DICTIONARY  = {
    "mb_header_fastecheck": True,
    "mb_dir_read_recursive": True
}

def check_last_and_update(last_indexed: List[FileDescriptor]) -> bool:
    
    return False

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
