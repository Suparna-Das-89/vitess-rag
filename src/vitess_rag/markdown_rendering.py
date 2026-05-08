import re
from typing import Dict, List, Optional, Tuple

from markdown_it.token import Token

from .text_utils import ANCHOR_TAG_RE, clean_whitespace, unique_preserve_order


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
