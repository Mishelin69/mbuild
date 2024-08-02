from typing import Any, List, IO, Tuple
import sys
import os

from header_file import HeaderFile
from file_descriptor import FileDescriptor
from enum import Enum

ALLOWED_SOURCE_EXTENSIONS: List[str] = [
    'c', 'cpp', 'cxx'
]

ALLOWED_HEADER_EXTENSIONS: List[str] = [
    'h', 'hpp', 'hxx'
]

type MBUILD_CONFIG_DICTIONARY = dict[str, Any]

SourceScan = Enum('SourceScan', ['function_def', 'n_lines'])

MBUILD_CONFIG: MBUILD_CONFIG_DICTIONARY  = {
    "mb_header_fastecheck": True,
    "mb_dir_read_recursive": True,
    "mb_dir_source_scan" : SourceScan.function_def,
    "n_lines": 0,
}

class LStrIntPair:

    def __init__(self, l: List[str], x: int) -> None:
        self.l = l
        self.x = x

#new version should actually speed things up for bigger inputs
#we avoid reallocating each time by just allocating once!
def source_parse_after_def(s: str, i: int) -> str:

    while s[i] != '<':
        i += 1

    i += 1
    l: int = i

    while s[i] != '>':
        i += 1
    
    return s[l:i]

def build_fd_from_list(f_names: List[str]) -> List[FileDescriptor]:

    #yes ik this is mostrosity
    return [FileDescriptor(x, os.stat(x).st_ctime) for x in f_names]

def source_scan_read_n(handle: IO, lines: int) -> List[FileDescriptor]:

    f_names: List[str] = []

    for _ in range(lines):

        line: str = handle.readline()
        pos: int = line.find("#define")

        if pos != -1:
            
            h_name: str = source_parse_after_def(line, pos)
            if h_name.endswith(tuple(ALLOWED_HEADER_EXTENSIONS)):
                f_names.append(h_name)
            
    return build_fd_from_list(f_names)

#scan till function definition (not just function declaration)
def source_scan_till_fd(handle: IO) -> List[FileDescriptor]:

    f_names: List[str] = []

    while True:

        line: str = handle.readline()
        #WHY WAS THERE #define in the first place? Like what the heck???!
        #thank god I found it before it ended a bit too bad T_T
        pos: int = line.find("#include")

        if pos != -1:
            
            h_name: str = source_parse_after_def(line, pos)
            if h_name.endswith(tuple(ALLOWED_HEADER_EXTENSIONS)):
                f_names.append(h_name)

        pos = line.find(')')        

        #check condition
        if pos != -1:

            condition: bool = False

            l_curly: int = 123 

            #check if next is curly or not
            while True:

                pos += 1

                if line[pos].isspace():
                    pos += 1
                    continue
                elif ord(line[pos]) == l_curly:
                    condition = True
                    break
                else:
                    break

            if condition:
                break

    return build_fd_from_list(f_names)


def read_all_current(paths: List[str], recursive: bool) -> List[HeaderFile]:

    headers_desc: List[HeaderFile] = []
    file_good_extension: List[str] = []
    file_good_source: List[str] = []

    #This should take all paths given and any subdirs and find 
    #file with preset extension (ALLOWED_HEADER_EXTIONS) 
    #will be modifiable in the future
    #TL;DR: filter header files from given directories and their subdirs (if set to true)
    #this is just a weird implementation of a "stack" I guess, now thinking about it
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
                    file_good_extension.append(os.path.abspath(_path))
                elif _path.endswith(ALLOWED_SOURCE_EXTENSIONS):
                    file_good_source.append(os.path.abspath(_path))

            s_index += 1
            p_layer.x = s_index

    print(file_good_extension)

    #build current header file fds and
    #search for edges with their positions/read from previous and search from that
    #method/condition for search in config !!!

    #damn we getting really rusty with this type abomination
    edges: List[List[FileDescriptor]] = []

    for x in file_good_source:

        with open(x, "r") as f:

            match (MBUILD_CONFIG["mb_dir_source_scan"]):

                case SourceScan.function_def:
                    edges.append(source_scan_till_fd(f))
                case SourceScan.n_lines:
                    edges.append(source_scan_read_n(f, MBUILD_CONFIG["n_lines"]))

    #safe check
    if len(file_good_source) != len(edges):
        print("Error: Something went wrong with scanning source files!\n\
                HINT: len(source) != len(edges)")

    #[edges] => header files
    #[source] => source files, source[0] ^ edges[o] => source file and header files pair
    #transform into header[0] = source files the header is in
    header_to_source: dict[FileDescriptor, List[FileDescriptor]] = {}

    for source, edge in zip(file_good_source, edges):
        for header in edge:

            if header not in header_to_source:
                header_to_source[header] = []

            #figure out how to check if source is already in there :) 
            #thinking about using sets and calling it a day
            header_to_source[header].append(FileDescriptor.create_from_name(source))
            
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
