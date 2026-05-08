import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from markdown_it import MarkdownIt
from markdown_it.token import Token

from .models import BaseChunk, EquationChunk, Metadata, TableChunk, TextChunk

MAX_TEXT_CHARS = 1200

ANCHOR_TAG_RE = re.compile(r'<a\s+id="([^"]+)"\s*>\s*</a>')
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")
HEADING_LINE_RE = re.compile(r"^(#{1,6})\s+(.*)$")
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

TABLE_CAPTION_HINT_RE = re.compile(
    r"(?:^table\b|following table|lists the parameters|lists the output|lists the example|lists the files)",
    re.IGNORECASE,
)


def clean_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_table_title(title: Optional[str]) -> Optional[str]:
    if not title:
        return None

    title = clean_whitespace(title)
    title = re.sub(r"^Table:\s*", "", title, flags=re.IGNORECASE)
    return title


def single_line(text: str) -> str:
    text = clean_whitespace(text).replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def slugify(text: str) -> str:
    text = clean_whitespace(text).lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_") or "untitled"


def strip_markdown_keep_visible_text(text: str) -> str:
    text = clean_whitespace(text)
    text = ANCHOR_TAG_RE.sub("", text)

    def replace_link(match: re.Match) -> str:
        label = match.group(1)
        target = match.group(2)

        if target.startswith("http://") or target.startswith("https://"):
            return f"{label} ({target})"

        return label

    text = MARKDOWN_LINK_RE.sub(replace_link, text)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"_([^_]+)_", r"\1", text)

    return clean_whitespace(text)


def looks_like_caption_text(text: str) -> bool:
    return bool(TABLE_CAPTION_HINT_RE.search(clean_whitespace(text)))


def extract_module_name(text: str) -> str:
    text = strip_markdown_keep_visible_text(text)
    match = re.search(r"'([^']+)'", text)

    if match:
        return clean_whitespace(match.group(1))

    return clean_whitespace(text)


def make_chunk_id(
    source_file: Optional[str],
    module: Optional[str],
    kind: str,
    idx: int,
) -> str:
    return f"{slugify(source_file or 'unknown')}__{slugify(module or 'root')}__{kind}__{idx}"


def unique_preserve_order(items: List[str]) -> List[str]:
    seen = set()
    out = []

    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)

    return out


def extract_anchor_ids(raw_text: str) -> List[str]:
    return ANCHOR_TAG_RE.findall(raw_text)


def render_inline_token_text(
    token: Token,
) -> Tuple[str, List[Dict[str, str]], List[str], List[str]]:
    if token.type != "inline":
        return clean_whitespace(token.content), [], [], []

    result_parts: List[str] = []
    links: List[Dict[str, str]] = []
    anchors: List[str] = []
    external_links: List[str] = []

    current_link_href: Optional[str] = None
    current_link_text_parts: List[str] = []

    def flush_link() -> None:
        nonlocal current_link_href, current_link_text_parts

        if current_link_href is not None:
            label = clean_whitespace("".join(current_link_text_parts))
            href = current_link_href.strip()

            if label:
                links.append({"label": label, "target": href})

                if href.startswith("http://") or href.startswith("https://"):
                    external_links.append(href)
                    result_parts.append(f"{label} ({href})")
                else:
                    result_parts.append(label)

        current_link_href = None
        current_link_text_parts = []

    for child in token.children or []:
        if child.type == "link_open":
            flush_link()
            current_link_href = dict(child.attrs or {}).get("href")
            current_link_text_parts = []

        elif child.type == "link_close":
            flush_link()

        elif child.type in {"text", "code_inline"}:
            if current_link_href is not None:
                current_link_text_parts.append(child.content)
            else:
                result_parts.append(child.content)

        elif child.type in {"softbreak", "hardbreak"}:
            if current_link_href is not None:
                current_link_text_parts.append("\n")
            else:
                result_parts.append("\n")

        elif child.type == "html_inline":
            anchors.extend(extract_anchor_ids(child.content or ""))

        elif child.content:
            if current_link_href is not None:
                current_link_text_parts.append(child.content)
            else:
                result_parts.append(child.content)

    flush_link()

    return (
        clean_whitespace("".join(result_parts)),
        links,
        anchors,
        unique_preserve_order(external_links),
    )


def is_table_line(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("|") and stripped.endswith("|")


def is_separator_row(line: str) -> bool:
    stripped = line.strip()

    if not is_table_line(stripped):
        return False

    parts = [p.strip() for p in stripped.strip("|").split("|")]

    if not parts:
        return False

    for part in parts:
        if not part:
            return False
        if any(ch not in ":-" for ch in part):
            return False
        if part.count("-") < 2:
            return False

    return True


def is_table_separator_line(line: str) -> bool:
    stripped = line.strip()

    if not stripped.startswith("|"):
        return False

    parts = [p.strip() for p in stripped.strip("|").split("|")]

    if len(parts) < 2:
        return False

    for part in parts:
        if not part:
            return False
        if any(ch not in "-: " for ch in part):
            return False
        if "-" not in part:
            return False

    return True


def split_table_row(line: str) -> List[str]:
    cells = line.strip().strip("|").split("|")
    return [single_line(strip_markdown_keep_visible_text(cell.strip())) for cell in cells]


def pad_row(row: List[str], width: int) -> List[str]:
    if len(row) < width:
        return row + [""] * (width - len(row))

    if len(row) > width:
        return row[:width]

    return row


def looks_like_second_header_row(row: List[str]) -> bool:
    nonempty = sum(bool(cell.strip()) for cell in row)

    if nonempty == 0:
        return False

    leading_empty = 0

    for cell in row:
        if cell.strip():
            break
        leading_empty += 1

    return leading_empty >= 1


def merge_header_rows(row1: List[str], row2: List[str]) -> List[str]:
    width = max(len(row1), len(row2))
    row1 = pad_row(row1, width)
    row2 = pad_row(row2, width)

    merged = []

    for left, right in zip(row1, row2):
        if left and right:
            merged.append(f"{left} / {right}")
        else:
            merged.append(left or right)

    return merged


def parse_table_from_lines(
    lines: List[str],
    start_idx: int,
) -> Optional[Dict[str, object]]:
    if start_idx + 1 >= len(lines):
        return None

    if not is_table_line(lines[start_idx]):
        return None

    if not is_separator_row(lines[start_idx + 1]):
        return None

    header1 = split_table_row(lines[start_idx])
    i = start_idx + 2

    header2 = None

    if i < len(lines) and is_table_line(lines[i]):
        candidate = split_table_row(lines[i])

        if looks_like_second_header_row(candidate):
            header2 = candidate
            i += 1

    descriptor = merge_header_rows(header1, header2) if header2 else header1
    width = len(descriptor)

    rows: List[List[str]] = []

    while i < len(lines) and is_table_line(lines[i]):
        if not is_separator_row(lines[i]):
            rows.append(pad_row(split_table_row(lines[i]), width))
        i += 1

    if not rows:
        return None

    return {
        "descriptor": descriptor,
        "rows": rows,
        "end_idx": i,
    }


def find_markdown_table_ranges_in_lines(lines: List[str]) -> List[Tuple[int, int]]:
    ranges: List[Tuple[int, int]] = []
    i = 0

    while i < len(lines) - 1:
        line = lines[i].strip()
        next_line = lines[i + 1].strip()

        if is_table_line(line) and is_table_separator_line(next_line):
            start = i
            i += 2

            while i < len(lines) and lines[i].strip():
                if is_table_line(lines[i].strip()):
                    i += 1
                else:
                    break

            ranges.append((start, i))
            continue

        i += 1

    return ranges


def remove_table_blocks_from_text(text: str) -> str:
    if not text:
        return text

    lines = text.splitlines()
    ranges = find_markdown_table_ranges_in_lines(lines)

    if not ranges:
        return text

    keep = [True] * len(lines)

    for start, end in ranges:
        for i in range(start, end):
            keep[i] = False

    cleaned_lines: List[str] = []
    prev_blank = False

    for idx, line in enumerate(lines):
        if not keep[idx]:
            if not prev_blank and cleaned_lines:
                cleaned_lines.append("")
                prev_blank = True
            continue

        if line.strip():
            cleaned_lines.append(line)
            prev_blank = False
        elif not prev_blank:
            cleaned_lines.append("")
            prev_blank = True

    return clean_whitespace("\n".join(cleaned_lines))


def find_table_caption(lines: List[str], table_start_idx: int) -> Optional[str]:
    j = table_start_idx - 1
    collected: List[str] = []

    while j >= 0:
        raw = lines[j]
        stripped = raw.strip()

        if not stripped:
            if collected:
                break
            j -= 1
            continue

        if is_table_line(stripped):
            break

        heading_match = HEADING_LINE_RE.match(stripped)

        if heading_match:
            heading_text = strip_markdown_keep_visible_text(heading_match.group(2))

            if looks_like_caption_text(heading_text):
                collected.append(heading_text)

            break

        collected.append(raw)
        j -= 1

    if not collected:
        return None

    text = strip_markdown_keep_visible_text("\n".join(reversed(collected)))

    if text and looks_like_caption_text(text):
        return text

    return None


def normalize_column_key(col_name: str, idx: int) -> str:
    key = slugify(col_name)

    if not key or key == "untitled":
        return f"col_{idx}"

    return key


def build_row_fields(descriptor: List[str], row: List[str]) -> Dict[str, str]:
    fields: Dict[str, str] = {}

    for idx, (col_name, cell) in enumerate(zip(descriptor, row), start=1):
        key = normalize_column_key(col_name, idx)
        fields[key] = single_line(cell)

    return fields


def extract_common_aliases(row_fields: Dict[str, str]) -> Dict[str, str]:
    aliases: Dict[str, str] = {}

    for key, value in row_fields.items():
        key_lower = key.lower()

        if "command" in key_lower and "option" in key_lower and value:
            aliases["command_option"] = value
        elif key_lower == "label" and value:
            aliases["label"] = value
        elif key_lower == "parameter" and value:
            aliases["parameter"] = value
        elif key_lower == "description" and value:
            aliases["description"] = value
        elif key_lower in {"notes", "note"} and value:
            aliases["notes"] = value
        elif key_lower in {"file", "filename"} and value:
            aliases["file"] = value
        elif key_lower == "coating" and value:
            aliases["coating"] = value
        elif key_lower in {"range_or_values", "range_values"} and value:
            aliases["range_or_values"] = value
        elif key_lower in {"col_1", "number"} and value:
            aliases["row_identifier"] = value

    return aliases


def is_heading_line(line: str) -> bool:
    return bool(HEADING_LINE_RE.match(line.strip()))


def build_table_chunk_content(
    columns: List[str],
    row: List[str],
) -> str:
    pairs = []

    for col_name, cell in zip(columns, row):
        col = clean_whitespace(col_name)
        val = single_line(cell)

        if col and val:
            pairs.append(f"{col}: {val}")
        elif col:
            pairs.append(f"{col}:")
        elif val:
            pairs.append(val)

    return " | ".join(pairs)


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


def write_jsonl(chunks: List[BaseChunk], output_file: str | Path) -> None:
    out = Path(output_file)

    with out.open("w", encoding="utf-8") as file:
        for chunk in chunks:
            file.write(json.dumps(chunk.model_dump(), ensure_ascii=False) + "\n")
