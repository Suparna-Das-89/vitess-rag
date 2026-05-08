import re
from typing import List, Optional

ANCHOR_TAG_RE = re.compile(r'<a\s+id="([^"]+)"\s*>\s*</a>')
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
