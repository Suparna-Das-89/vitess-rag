import json
from pathlib import Path
from typing import List

from .models import BaseChunk


def write_jsonl(chunks: List[BaseChunk], output_file: str | Path) -> None:
    out = Path(output_file)

    with out.open("w", encoding="utf-8") as file:
        for chunk in chunks:
            file.write(json.dumps(chunk.model_dump(), ensure_ascii=False) + "\n")
