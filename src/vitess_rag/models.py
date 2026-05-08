from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class Metadata(BaseModel):
    module: Optional[str] = None
    section: Optional[str] = None
    subsection: Optional[str] = None
    subsubsection: Optional[str] = None
    source_file: Optional[str] = None
    is_pre_table_text: bool = False
    is_code_block: bool = False


class BaseChunk(BaseModel):
    chunk_id: str
    chunk_type: Literal["text", "table", "equation"]
    metadata: Metadata
    content: str
    external_links: Optional[List[str]] = None


class TextChunk(BaseChunk):
    chunk_type: Literal["text"] = "text"


class TableChunk(BaseChunk):
    chunk_type: Literal["table"] = "table"
    descriptor: List[str]
    table_title: Optional[str] = None
    row_fields: Dict[str, str] = Field(default_factory=dict)


class EquationChunk(BaseChunk):
    chunk_type: Literal["equation"] = "equation"
