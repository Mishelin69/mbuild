from __future__ import annotations
from dataclasses import dataclass
import os

type FileName = str
type UTC = float

@dataclass(frozen=True)
class FileDescriptor:

    file_name: FileName
    st_ctime: UTC

    @classmethod
    def create_from_data(cls, file_name: FileName, st_ctime: UTC) -> FileDescriptor:
        return cls(file_name, st_ctime)

    @classmethod
    def create_from_name(cls, file_name: FileName) -> FileDescriptor:
        return cls(file_name, os.path.getctime(file_name))

    def __str__(self) -> str:
        return self.file_name
