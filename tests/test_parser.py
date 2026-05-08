from vitess_rag.parser import parse_markdown_document


def test_parse_text_chunk():
    md = "# Module A\n\nThis is a paragraph."

    chunks = parse_markdown_document(md, source_file="test.md")

    assert len(chunks) == 1
    assert chunks[0].chunk_type == "text"
    assert chunks[0].metadata.module == "Module A"
    assert chunks[0].content == "This is a paragraph."


def test_parse_table_chunks():
    md = """
# Module A

| Command option | Description |
| --- | --- |
| -z | Example option |
| -A | Another option |
"""

    chunks = parse_markdown_document(md, source_file="test.md")
    table_chunks = [chunk for chunk in chunks if chunk.chunk_type == "table"]

    assert len(table_chunks) == 2
    assert table_chunks[0].chunk_type == "table"
    assert table_chunks[0].row_fields["command_option"] == "-z"
    assert table_chunks[0].row_fields["description"] == "Example option"


def test_heading_metadata():
    md = """
# Module A

## Section B

### Subsection C

Some content.
"""

    chunks = parse_markdown_document(md, source_file="test.md")

    assert chunks[0].metadata.module == "Module A"
    assert chunks[0].metadata.section == "Section B"
    assert chunks[0].metadata.subsection == "Subsection C"
