import re
from typing import Dict, List, Optional, Tuple

ANCHOR_TAG_RE = re.compile(r'<a\s+id="([^"]+)"\s*>\s*</a>')
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

INLINE_EQ_RE = re.compile(r"(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)")
MATH_PLACEHOLDER_RE = re.compile(r"@@MATH(?:INLINE|BLOCK)\d+@@")

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


def replace_math_with_placeholders(
    md_text: str,
) -> Tuple[str, Dict[str, Dict[str, str]]]:
    math_map: Dict[str, Dict[str, str]] = {}
    counter = 1

    def store(body: str, kind: str) -> str:
        nonlocal counter

        if kind == "inline":
            placeholder = f"@@MATHINLINE{counter}@@"
        else:
            placeholder = f"@@MATHBLOCK{counter}@@"

        math_map[placeholder] = {
            "latex": body.strip(),
            "kind": kind,
        }

        counter += 1
        return placeholder

    lines = md_text.splitlines()
    rebuilt: List[str] = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if line in {"$$", "$"}:
            delimiter = line
            j = i + 1
            body: List[str] = []

            while j < len(lines) and lines[j].strip() != delimiter:
                body.append(lines[j])
                j += 1

            if j < len(lines):
                rebuilt.append(store("\n".join(body), "block"))
                i = j + 1
                continue

        rebuilt.append(lines[i])
        i += 1

    text = "\n".join(rebuilt)

    def repl_inline(match: re.Match) -> str:
        return store(match.group(1), "inline")

    text = INLINE_EQ_RE.sub(repl_inline, text)

    return text, math_map


def restore_inline_math(
    text: str,
    math_map: Dict[str, Dict[str, str]],
) -> str:
    for placeholder, payload in math_map.items():
        if payload["kind"] == "inline":
            text = text.replace(placeholder, f"${payload['latex']}$")
        else:
            text = text.replace(placeholder, payload["latex"])

    return text


def is_only_math_placeholder(text: str) -> Optional[str]:
    text = text.strip()

    if MATH_PLACEHOLDER_RE.fullmatch(text):
        return text

    return None
