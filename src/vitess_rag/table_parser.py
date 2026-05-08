import re
from typing import Dict, List, Optional, Tuple

from .text_utils import (
    clean_whitespace,
    looks_like_caption_text,
    single_line,
    slugify,
    strip_markdown_keep_visible_text,
)

HEADING_LINE_RE = re.compile(r"^(#{1,6})\s+(.*)$")


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
