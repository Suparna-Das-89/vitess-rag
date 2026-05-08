from vitess_rag.chroma import chunks_to_chroma_inputs
from vitess_rag.parser import parse_markdown_document


def test_chunks_to_chroma_inputs():
    md = "# Module A\n\nSome content."
    chunks = parse_markdown_document(md, source_file="test.md")

    ids, documents, metadatas = chunks_to_chroma_inputs(chunks)

    assert len(ids) == 1
    assert len(documents) == 1
    assert len(metadatas) == 1
    assert metadatas[0]["module"] == "Module A"
    assert metadatas[0]["chunk_type"] == "text"
