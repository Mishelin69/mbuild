from __future__ import annotations
from dataclasses import dataclass

type FileName = str
type UTC = float

@dataclass(frozen=True)
class FileDescriptor:

    file_name: FileName
    st_mtime: UTC

    @classmethod
    def create_from_data(cls, file_name: FileName, st_mtime: UTC) -> FileDescriptor:
        return cls(file_name, st_mtime)
