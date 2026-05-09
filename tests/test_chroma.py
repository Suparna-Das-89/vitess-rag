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


def test_table_row_fields_are_flattened_to_chroma_metadata():
    md = """
# VITESS Module Filter

| Parameter Unit | Description | Range or Values | Command Option |
| --- | --- | --- | --- |
| filter parameter 4 | keeps trajectories | none, posy | -L |
"""

    chunks = parse_markdown_document(md, source_file="filter.md")
    ids, documents, metadatas = chunks_to_chroma_inputs(chunks)

    assert len(ids) == 1
    assert len(documents) == 1
    assert len(metadatas) == 1

    assert metadatas[0]["chunk_type"] == "table"
    assert metadatas[0]["row_parameter_unit"] == "filter parameter 4"
    assert metadatas[0]["row_description"] == "keeps trajectories"
    assert metadatas[0]["row_range_or_values"] == "none, posy"
    assert metadatas[0]["row_command_option"] == "-L"
