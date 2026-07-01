import json
from pathlib import Path
from typing import Dict, List, Tuple

import chromadb

from .io import write_jsonl
from .models import BaseChunk, Metadata, TableChunk
from .parser import parse_markdown_document


def build_path(
    module: str | None,
    section: str | None,
    subsection: str | None,
    subsubsection: str | None,
) -> str:
    parts = [p for p in [module, section, subsection, subsubsection] if p]
    return " > ".join(parts)


def enrich_text_for_chroma(content: str, metadata: Metadata) -> str:
    parts = []

    if metadata.module:
        parts.append(f"Module: {metadata.module}")
    if metadata.section:
        parts.append(f"Section: {metadata.section}")
    if metadata.subsection:
        parts.append(f"Subsection: {metadata.subsection}")
    if metadata.subsubsection:
        parts.append(f"Subsubsection: {metadata.subsubsection}")

    parts.append(content)

    return " | ".join(parts)


def enrich_table_for_chroma(chunk: TableChunk) -> str:
    metadata = chunk.metadata
    parts = []

    if metadata.module:
        parts.append(f"Module: {metadata.module}")
    if metadata.section:
        parts.append(f"Section: {metadata.section}")
    if metadata.subsection:
        parts.append(f"Subsection: {metadata.subsection}")
    if metadata.subsubsection:
        parts.append(f"Subsubsection: {metadata.subsubsection}")
    if chunk.table_title:
        parts.append(f"Table: {chunk.table_title}")

    parts.append(chunk.content)

    return " | ".join(parts)


def chunk_to_chroma_record(chunk: BaseChunk) -> Dict[str, object]:
    metadata = chunk.metadata

    if isinstance(chunk, TableChunk):
        document = enrich_table_for_chroma(chunk)
    else:
        document = enrich_text_for_chroma(chunk.content, metadata)

    path = build_path(
        metadata.module,
        metadata.section,
        metadata.subsection,
        metadata.subsubsection,
    )

    chroma_metadata: Dict[str, object] = {
        "chunk_type": chunk.chunk_type,
        "module": metadata.module or "",
        "section": metadata.section or "",
        "subsection": metadata.subsection or "",
        "subsubsection": metadata.subsubsection or "",
        "source_file": metadata.source_file or "",
        "path": path,
        "is_pre_table_text": metadata.is_pre_table_text,
        "is_code_block": metadata.is_code_block,
    }

    if isinstance(chunk, TableChunk):
        chroma_metadata["table_descriptor"] = " | ".join(chunk.descriptor)
        chroma_metadata["table_title"] = chunk.table_title or ""
        chroma_metadata["row_fields_json"] = json.dumps(
            chunk.row_fields,
            ensure_ascii=False,
        )

        for key, value in chunk.row_fields.items():
            if value:
                chroma_metadata[f"row_{key}"] = value

    return {
        "id": chunk.chunk_id,
        "document": document,
        "metadata": chroma_metadata,
    }


def chunks_to_chroma_inputs(
    chunks: List[BaseChunk],
) -> Tuple[List[str], List[str], List[Dict[str, object]]]:
    records = [chunk_to_chroma_record(chunk) for chunk in chunks]

    ids = [str(record["id"]) for record in records]
    documents = [str(record["document"]) for record in records]
    metadatas = [record["metadata"] for record in records]

    return ids, documents, metadatas


def build_chunks_from_directory(
    input_dir: str | Path,
    output_jsonl: str | Path | None = None,
) -> List[BaseChunk]:
    input_path = Path(input_dir)

    if not input_path.exists():
        raise FileNotFoundError(f"Input directory not found: {input_path.resolve()}")

    md_files = sorted(input_path.glob("*.md"))

    if not md_files:
        raise FileNotFoundError(f"No markdown files found in: {input_path.resolve()}")

    all_chunks: List[BaseChunk] = []

    for md_file in md_files:
        md_text = md_file.read_text(encoding="utf-8")

        chunks = parse_markdown_document(
            md_text=md_text,
            source_file=md_file.name,
        )
        print(md_file.name, len(chunks))
        for chunk in chunks:
            chunk.content = chunk.content.replace("\n", " ").strip()

        all_chunks.extend(chunks)

    if output_jsonl:
        write_jsonl(all_chunks, output_jsonl)

    return all_chunks


def get_or_create_collection(
    persist_path: str | Path,
    collection_name: str,
    embedding_function,
    recreate: bool = False,
):
    client = chromadb.PersistentClient(path=str(persist_path))

    if recreate:
        try:
            client.delete_collection(collection_name)
        except Exception:
            pass

    return client.get_or_create_collection(
        name=collection_name,
        embedding_function=embedding_function,
    )


def index_markdown_directory(
    input_dir: str | Path,
    persist_path: str | Path = "chroma_db",
    collection_name: str = "vitess_docs_blablador_v3",
    embedding_function=None,
    output_jsonl: str | Path | None = "all_modules_chunks.jsonl",
    recreate: bool = True,
):
    if embedding_function is None:
        from .embeddings import BlabladorEmbeddingFunction

        embedding_function = BlabladorEmbeddingFunction()

    chunks = build_chunks_from_directory(
        input_dir=input_dir,
        output_jsonl=output_jsonl,
    )

    ids, documents, metadatas = chunks_to_chroma_inputs(chunks)

    collection = get_or_create_collection(
        persist_path=persist_path,
        collection_name=collection_name,
        embedding_function=embedding_function,
        recreate=recreate,
    )

    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
    )

    return collection, chunks
