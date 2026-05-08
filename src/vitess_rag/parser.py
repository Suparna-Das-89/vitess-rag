import re
from typing import List, Optional

from markdown_it import MarkdownIt

from .markdown_rendering import extract_anchor_ids, render_inline_token_text
from .models import BaseChunk, EquationChunk, Metadata, TableChunk, TextChunk
from .table_parser import (
    build_row_fields,
    build_table_chunk_content,
    extract_common_aliases,
    find_table_caption,
    is_heading_line,
    parse_table_from_lines,
    remove_table_blocks_from_text,
)
from .text_utils import (
    clean_whitespace,
    extract_module_name,
    make_chunk_id,
    normalize_table_title,
    unique_preserve_order,
)

MAX_TEXT_CHARS = 1200
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")


class MarkdownChunkParser:
    def __init__(
        self,
        source_file: str,
        max_text_chars: int = MAX_TEXT_CHARS,
    ):
        self.source_file = source_file
        self.max_text_chars = max_text_chars
        self.md = MarkdownIt("commonmark", {"html": True})

        self.chunks: List[BaseChunk] = []
        self.chunk_index = 0

        self.module_name: Optional[str] = None
        self.section: Optional[str] = None
        self.subsection: Optional[str] = None
        self.subsubsection: Optional[str] = None

        self.pending_table_title: Optional[str] = None

    def build_metadata(
        self,
        is_pre_table_text: bool = False,
        is_code_block: bool = False,
    ) -> Metadata:
        return Metadata(
            module=self.module_name,
            section=self.section,
            subsection=self.subsection,
            subsubsection=self.subsubsection,
            source_file=self.source_file,
            is_pre_table_text=is_pre_table_text,
            is_code_block=is_code_block,
        )

    def next_chunk_id(self, kind: str) -> str:
        return make_chunk_id(
            self.source_file,
            self.module_name,
            kind,
            self.chunk_index,
        )

    def split_text(self, text: str) -> List[str]:
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        out: List[str] = []
        current = ""

        def flush() -> None:
            nonlocal current

            if current.strip():
                out.append(current.strip())

            current = ""

        for para in paragraphs:
            bullet_parts = re.split(r"\n(?=-\s+)", para)

            for bullet_para in bullet_parts:
                bullet_para = bullet_para.strip()

                if not bullet_para:
                    continue

                if len(bullet_para) <= self.max_text_chars:
                    candidate = bullet_para if not current else f"{current}\n\n{bullet_para}"

                    if len(candidate) <= self.max_text_chars:
                        current = candidate
                    else:
                        flush()
                        current = bullet_para

                    continue

                sentences = [
                    sentence.strip()
                    for sentence in SENTENCE_SPLIT_RE.split(bullet_para)
                    if sentence.strip()
                ]

                if not sentences:
                    sentences = [bullet_para]

                for sentence in sentences:
                    if len(sentence) <= self.max_text_chars:
                        candidate = sentence if not current else f"{current} {sentence}"

                        if len(candidate) <= self.max_text_chars:
                            current = candidate
                        else:
                            flush()
                            current = sentence
                    else:
                        flush()
                        start = 0

                        while start < len(sentence):
                            piece = sentence[start:start + self.max_text_chars].strip()

                            if piece:
                                out.append(piece)

                            start += self.max_text_chars

        flush()
        return out

    def emit_text(
        self,
        text: str,
        is_pre_table_text: bool = False,
        is_code_block: bool = False,
        external_links: Optional[List[str]] = None,
    ) -> None:
        text = clean_whitespace(text)

        if not text:
            return

        text = remove_table_blocks_from_text(text)

        if not text:
            return

        external_links = unique_preserve_order(external_links or [])

        for part in self.split_text(text):
            cleaned_part = clean_whitespace(part)

            if not cleaned_part:
                continue

            self.chunks.append(
                TextChunk(
                    chunk_id=self.next_chunk_id("text"),
                    metadata=self.build_metadata(
                        is_pre_table_text=is_pre_table_text,
                        is_code_block=is_code_block,
                    ),
                    content=cleaned_part,
                    external_links=external_links or None,
                )
            )

            self.chunk_index += 1

    def emit_equation(self, equation_text: str) -> None:
        equation_text = equation_text.strip()

        if not equation_text:
            return

        self.chunks.append(
            EquationChunk(
                chunk_id=self.next_chunk_id("equation"),
                metadata=self.build_metadata(),
                content=equation_text,
            )
        )

        self.chunk_index += 1

    def emit_table_chunks(
        self,
        descriptor: List[str],
        rows: List[List[str]],
        table_title: Optional[str] = None,
    ) -> None:
        if not descriptor or not rows:
            return

        cleaned_descriptor = [clean_whitespace(col) for col in descriptor]
        normalized_title = normalize_table_title(table_title)

        for row in rows:
            row_fields = build_row_fields(cleaned_descriptor, row)
            row_aliases = extract_common_aliases(row_fields)
            final_row_fields = {**row_fields, **row_aliases}

            row_content = build_table_chunk_content(
                columns=cleaned_descriptor,
                row=row,
            )

            external_links = unique_preserve_order([
                url
                for cell in row
                for url in re.findall(r"https?://\S+", cell)
            ])

            self.chunks.append(
                TableChunk(
                    chunk_id=self.next_chunk_id("table"),
                    metadata=self.build_metadata(),
                    content=f"Row: {row_content}",
                    descriptor=cleaned_descriptor,
                    table_title=normalized_title,
                    row_fields=final_row_fields,
                    external_links=external_links or None,
                )
            )

            self.chunk_index += 1

    def heading_directly_introduces_table(
        self,
        lines: List[str],
        heading_idx: int,
    ) -> bool:
        i = heading_idx + 1

        while i < len(lines):
            stripped = lines[i].strip()

            if not stripped:
                i += 1
                continue

            if is_heading_line(stripped):
                return False

            return parse_table_from_lines(lines, i) is not None

        return False

    def set_heading(
        self,
        level: int,
        heading_text: str,
        lines: List[str],
        line_idx: int,
    ) -> None:
        heading_text = clean_whitespace(heading_text)

        if not heading_text:
            return

        if level == 1:
            self.module_name = extract_module_name(heading_text)
            self.section = None
            self.subsection = None
            self.subsubsection = None
            self.pending_table_title = None
            return

        if level in {2, 3, 4} and self.heading_directly_introduces_table(lines, line_idx):
            self.pending_table_title = heading_text
            return

        self.pending_table_title = None

        if level == 2:
            self.section = heading_text
            self.subsection = None
            self.subsubsection = None
        elif level == 3:
            self.subsection = heading_text
            self.subsubsection = None
        elif level == 4:
            self.subsubsection = heading_text

    def process_markdown_block(
        self,
        block_lines: List[str],
        original_lines: List[str],
        start_line_idx: int,
    ) -> None:
        text = "\n".join(block_lines).strip()

        if not text:
            return

        tokens = self.md.parse(text)
        i = 0

        while i < len(tokens):
            tok = tokens[i]

            if tok.type == "heading_open":
                level = int(tok.tag[1])

                if i + 1 < len(tokens) and tokens[i + 1].type == "inline":
                    heading_text, _, _, _ = render_inline_token_text(tokens[i + 1])

                    local_map = tok.map
                    abs_line_idx = (
                        start_line_idx + local_map[0]
                        if local_map
                        else start_line_idx
                    )

                    self.set_heading(level, heading_text, original_lines, abs_line_idx)
                    i += 3
                    continue

            if tok.type == "paragraph_open":
                if i + 1 < len(tokens) and tokens[i + 1].type == "inline":
                    text_out, _, _, external_links = render_inline_token_text(tokens[i + 1])

                    self.emit_text(
                        text_out,
                        is_pre_table_text=bool(self.pending_table_title),
                        external_links=external_links,
                    )

                    i += 3
                    continue

            if tok.type == "html_block":
                anchors = extract_anchor_ids(tok.content or "")

                if anchors:
                    i += 1
                    continue

            if tok.type in {"fence", "code_block"}:
                code_text = tok.content or ""

                if code_text.strip():
                    self.emit_text(
                        code_text,
                        is_code_block=True,
                    )

                i += 1
                continue

            i += 1

    def parse_document(self, md_text: str) -> None:
        lines = md_text.splitlines()
        i = 0
        buffer: List[str] = []
        buffer_start_idx: Optional[int] = None

        def flush_buffer() -> None:
            nonlocal buffer, buffer_start_idx

            if buffer:
                self.process_markdown_block(
                    block_lines=buffer,
                    original_lines=lines,
                    start_line_idx=buffer_start_idx if buffer_start_idx is not None else 0,
                )

                buffer = []
                buffer_start_idx = None

        while i < len(lines):
            line = lines[i]

            parsed_table = parse_table_from_lines(lines, i)

            if parsed_table:
                flush_buffer()

                raw_title = self.pending_table_title or find_table_caption(lines, i)
                table_title = normalize_table_title(raw_title)

                self.emit_table_chunks(
                    descriptor=parsed_table["descriptor"],
                    rows=parsed_table["rows"],
                    table_title=table_title,
                )

                self.pending_table_title = None
                i = parsed_table["end_idx"]
                continue

            if is_heading_line(line):
                flush_buffer()
                buffer_start_idx = i
                buffer.append(line)
                flush_buffer()
                i += 1
                continue

            if buffer_start_idx is None:
                buffer_start_idx = i

            buffer.append(line)
            i += 1

        flush_buffer()


def merge_adjacent_text_chunks(
    chunks: List[BaseChunk],
    max_chars: int = MAX_TEXT_CHARS,
) -> List[BaseChunk]:
    merged: List[BaseChunk] = []

    for chunk in chunks:
        if (
            merged
            and chunk.chunk_type == "text"
            and merged[-1].chunk_type == "text"
            and chunk.metadata.module == merged[-1].metadata.module
            and chunk.metadata.section == merged[-1].metadata.section
            and chunk.metadata.subsection == merged[-1].metadata.subsection
            and chunk.metadata.subsubsection == merged[-1].metadata.subsubsection
            and chunk.metadata.is_pre_table_text == merged[-1].metadata.is_pre_table_text
            and chunk.metadata.is_code_block == merged[-1].metadata.is_code_block
            and (chunk.external_links or []) == (merged[-1].external_links or [])
        ):
            previous = merged[-1]
            candidate = f"{previous.content} {chunk.content}"
            candidate = re.sub(r"\s+", " ", candidate).strip()

            if len(candidate) <= max_chars:
                previous.content = candidate
                continue

        merged.append(chunk)

    return merged


def parse_markdown_document(
    md_text: str,
    source_file: str = "unknown.md",
) -> List[BaseChunk]:
    md_text = md_text.replace("\ufeff", "")

    parser = MarkdownChunkParser(
        source_file=source_file,
        max_text_chars=MAX_TEXT_CHARS,
    )

    parser.parse_document(md_text)

    return merge_adjacent_text_chunks(parser.chunks, max_chars=MAX_TEXT_CHARS)
