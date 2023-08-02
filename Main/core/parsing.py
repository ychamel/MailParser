from io import BytesIO
from time import sleep
from typing import List, Any, Optional
import re
import streamlit as st
from pypdf import PdfReader
import extract_msg

import docx2txt
from langchain.docstore.document import Document
import fitz
from hashlib import md5

from abc import abstractmethod, ABC
from copy import deepcopy

from Main.core.PDF_Parser import parse_img, fetch_text


class File(ABC):
    """Represents an uploaded file comprised of Documents"""

    def __init__(
            self,
            name: str,
            id: str,
            metadata: Optional[dict[str, Any]] = None,
            docs: Optional[List[Document]] = None,
    ):
        self.name = name
        self.id = id
        self.metadata = metadata or {}
        self.docs = docs or []

    @classmethod
    @abstractmethod
    def from_bytes(cls, file: BytesIO) -> "File":
        """Creates a File from a BytesIO object"""

    def __repr__(self) -> str:
        return (
            f"File(name={self.name}, id={self.id},"
            " metadata={self.metadata}, docs={self.docs})"
        )

    def __str__(self) -> str:
        return f"File(name={self.name}, id={self.id}, metadata={self.metadata})"

    def copy(self) -> "File":
        """Create a deep copy of this File"""
        return self.__class__(
            name=self.name,
            id=self.id,
            metadata=deepcopy(self.metadata),
            docs=deepcopy(self.docs),
        )


def strip_consecutive_newlines(text: str) -> str:
    """Strips consecutive newlines from a string
    possibly with whitespace in between
    """
    return re.sub(r"\s*\n\s*", "\n", text)


class DocxFile(File):
    @classmethod
    def from_bytes(cls, file: BytesIO) -> "DocxFile":
        text = docx2txt.process(file)
        text = strip_consecutive_newlines(text)
        doc = Document(page_content=text.strip())
        return cls(name=file.name, id=md5(file.read()).hexdigest(), docs=[doc])


class PdfFile(File):
    @classmethod
    def from_bytes(cls, file: BytesIO) -> "PdfFile":
        pdf = fitz.open(stream=file.read(), filetype="pdf")  # type: ignore
        docs = []
        uuids = {}
        parsing_bar = st.progress(0.0, text="progress")
        size = len(pdf)
        for i, page in enumerate(pdf):
            text = page.get_text(sort=True)
            text = strip_consecutive_newlines(text)
            doc = Document(page_content=text.strip())
            doc.metadata["page"] = i + 1
            docs.append(doc)
            # update progress
            parsing_bar.progress(i / size, "Parsing PDF")
        # file.read() mutates the file object, which can affect caching
        # so we need to reset the file pointer to the beginning
        file.seek(0)
        return cls(name=file.name, id=md5(file.read()).hexdigest(), docs=docs)


class TxtFile(File):
    @classmethod
    def from_bytes(cls, file: BytesIO) -> "TxtFile":
        text = file.read().decode("utf-8")
        text = strip_consecutive_newlines(text)
        file.seek(0)
        doc = Document(page_content=text.strip())
        return cls(name=file.name, id=md5(file.read()).hexdigest(), docs=[doc])


class MsgFile(File):
    @classmethod
    def from_bytes(cls, file: BytesIO) -> "MsgFile":
        msg = extract_msg.Message(file)
        data = {
            "Sender": msg.sender,
            "Date": msg.date,
            "Subject": msg.subject,
        }
        text = msg.body
        doc = Document(page_content=text.strip())
        file.seek(0)
        return cls(name=file.name, id=md5(file.read()).hexdigest(), metadata=data, docs=[doc])


def read_file(file: BytesIO) -> File:
    """Reads an uploaded file and returns a File object"""
    if file.name.lower().endswith(".docx"):
        return DocxFile.from_bytes(file)
    elif file.name.lower().endswith(".pdf"):
        return PdfFile.from_bytes(file)
    elif file.name.lower().endswith(".txt"):
        return TxtFile.from_bytes(file)
    elif file.name.lower().endswith(".msg"):
        return MsgFile.from_bytes(file)
    else:
        raise NotImplementedError(f"File type {file.name.split('.')[-1]} not supported")
