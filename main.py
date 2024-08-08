from typing import Any, Generator, List, IO, Set, Tuple
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
    return [FileDescriptor(x, os.stat(x).st_birthtime) for x in f_names]

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

        #forgot this pretty important check yk
        if not line:
            print("WARNING: EMPTY FILE!")
            break

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

def listdir_abspath(dir: str) -> Generator[str, None, None]:

    if not os.path.isdir(dir):
        print(f"PATH IS NOT A DIR!!!!\n{dir}")
        exit(-1)

    for dirpath, dirnames, filenames in os.walk(dir):

        for d in dirnames:
            yield os.path.abspath(os.path.join(dirpath, d))

        for f in filenames:
            yield os.path.abspath(os.path.join(dirpath, f))


def build_header_to_source_relation(source_files: List[str]) -> List[HeaderFile]:

    headers_desc: List[HeaderFile] = []

    print(source_files)

    #build current header file fds and
    #search for edges with their positions/read from previous and search from that
    #method/condition for search in config !!!

    #damn we getting really rusty with this type abomination
    edges: List[List[FileDescriptor]] = []

    for x in source_files:

        with open(x, "r") as f:

            match (MBUILD_CONFIG["mb_dir_source_scan"]):

                case SourceScan.function_def:
                    edges.append(source_scan_till_fd(f))
                case SourceScan.n_lines:
                    edges.append(source_scan_read_n(f, MBUILD_CONFIG["n_lines"]))

    #safe check
    if len(source_files) != len(edges):
        print("Error: Something went wrong with scanning source files!\n\
                HINT: len(source) != len(edges)")

    #[edges] => header files
    #[source] => source files, source[0] ^ edges[o] => 
    #source file and header files pair
    #transform into header[0] = source files the header is in

    #thinking about it, this can kind of lead to problems I guess
    #yes it lead to issues and it sucks 
    #they're diff instances so they hash differently
    #(solution is to use strings as keys)
    header_to_source: dict[str, Tuple[FileDescriptor, List[FileDescriptor]]] = {}
    header_check_copy: dict[str, List[str]] = {}

    for source, edge in zip(source_files, edges):
        for header in edge:

            if header.file_name not in header_check_copy:
                header_check_copy[header.file_name] = []

            if source in header_check_copy[header.file_name]:
                continue
            else:
                header_check_copy[header.file_name].append(source)

            if header.file_name not in header_to_source:
                header_to_source[header.file_name] = (header, [])

            #figure out how to check if source is already in there :) 
            #thinking about using sets and calling it a day
            #1 => List[FileDescriptor]
            header_to_source[header.file_name][1].append(FileDescriptor.create_from_name(source))

    #testing will happen when Ill feel like it D: (tomorrow)
    for x in header_to_source.values():

        headers_desc.append(HeaderFile(x[0], x[1]))
            
    return headers_desc

def read_all_dirs(paths: List[str], recursive: bool) -> Tuple[Set[str], List[str]]:

    file_good_extension: Set[str] = set() 
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
        p_stack.append(LStrIntPair(list(listdir_abspath(p)), 0))
        p_index: int = 0
        s_index: int = 0

        while len(p_stack) >= 1:

            #if we reach end of path branch move back up (pop)
            if s_index == len(p_stack[p_index].l):
                p_index -= 1

                if p_index < 0:
                    break

                s_index = p_stack[p_index].x
                p_stack.pop()

            p_layer: LStrIntPair = p_stack[p_index]
            _path: str = p_layer.l[s_index]

            #index into paths (push)
            if recursive and os.path.isdir(_path):
                p_stack.append(LStrIntPair(list(listdir_abspath(_path)), 0))
                p_layer.x += 1
                s_index = 0
                p_index += 1

                continue

            else:
                #commented out for now :)
                #if _path.endswith(tuple(ALLOWED_HEADER_EXTENSIONS)):
                    #file_good_extension.add(os.path.abspath(_path))
                if _path.endswith(tuple(ALLOWED_SOURCE_EXTENSIONS)):
                    file_good_source.append(os.path.abspath(_path))

            s_index += 1
            p_layer.x = s_index


    return (file_good_extension, file_good_source)

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

def source_files_recompile(reader_list: List[HeaderFile], source_files: List[str], 
                    header_files: Set[str]) -> Tuple[Set[FileDescriptor], List[HeaderFile]]:

    #this will do a lot of heavylifting

    #> get old source fds compare to current
    #> if a files appears to be deleted/moved just remove it from reader_list
    #> if a file was moved it'll be found later on
    #> if any changes found to a source file add to a "new edges" list 
    #- also add to recompile and "ignore"
    #> if any new files are found, add to a "new edges" list
    #- also add to recompile and "ignore"
    #> build "new" edges
    #> from that build new HeaderFile list
    #> this should account for any new HeaderFiles / changes made to source files
    #? in the case of whole new Header that would mean add all sources to recompile and "ignore"
    #- use "sliding window" to keep the track of the og ones and isolate them for later checking
    #? if a HeaderFile happens to be in both of the lists, it'll get handled by the next step
    #- all of the source that could lead it in there, were already added so no problemo here
    #> "aggregate" the lists now
    #> head(er) time yay :)
    #> compare current st_mtimes with old ones, if != add every corresponding source
    #- but check against the "ignore" list first
    #> this will also return the updated HeaderFile list
    
    return (set(), [])

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


    current_file_good_extension, current_file_good_source = read_all_dirs(DESTINATION_DIRS, True)
    reader_list: List[HeaderFile] = read_all_indexed_last()

    if len(reader_list) == 0:

        #test place yk
        read_current: List[HeaderFile] = build_header_to_source_relation(current_file_good_source)

        #print(reader_list[0])
        print(read_current)

        #compile everything, link, write stuff to a file, etc 
        #the easier case to handle but obviously should on happen
        #on fresh inits of "system"

    else:
        #otherwise we don't read the whole thing and just do a shallow read (i.e. not read everything)
        #this alsoo needs a rewrite so the "interface" is a bit nicer
        #the design is sort of fine for now makes sense but it's a bit confusing
        #I need to clean up and maybe split to a different class
        #at this point its a big ass main file with no organization whatsoever

        # => figure out what needs to get recompiled
        # => recompile -> link -> whatever
        # => generate new HeaderFile list
        # => write the new data into a list

        need_recompile: Set[FileDescriptor] = source_files_recompile(
                reader_list, current_file_good_source, current_file_good_extension)

        pass
        #I wish I could use the unimplemented macro

    return 0

if __name__ == '__main__':
    main()
