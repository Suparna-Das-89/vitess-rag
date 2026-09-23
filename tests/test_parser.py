from vitess_rag.parser import parse_markdown_document


def test_parse_basic_text_chunk():
    md = """
# VITESS Module Filter

This module filters trajectories.
"""

    chunks = parse_markdown_document(md, source_file="filter.md")

    assert len(chunks) == 1
    assert chunks[0].chunk_type == "text"
    assert chunks[0].metadata.module == "VITESS Module Filter"
    assert chunks[0].content == "This module filters trajectories."


def test_heading_hierarchy_with_subsubsection():
    md = """
# VITESS Module Filter

## Section A

### Subsection B

#### Subsubsection C

Some content.
"""

    chunks = parse_markdown_document(md, source_file="filter.md")
    first = chunks[0]

    assert first.metadata.module == "VITESS Module Filter"
    assert first.metadata.section == "Section A"
    assert first.metadata.subsection == "Subsection B"
    assert first.metadata.subsubsection == "Subsubsection C"


def test_table_row_fields_like_real_jsonl():
    md = """
# VITESS Module Filter

The following table lists the parameters of the module 'filter'.

| Parameter Unit | Description | Range or Values | Command Option |
| --- | --- | --- | --- |
| filter parameter 4 | 4th parameter determining which trajectories are kept | none, posy, posz | -L |
"""

    chunks = parse_markdown_document(md, source_file="filter.md")
    table_chunks = [chunk for chunk in chunks if chunk.chunk_type == "table"]

    assert len(table_chunks) == 1

    row = table_chunks[0]

    assert row.chunk_type == "table"
    assert row.metadata.module == "VITESS Module Filter"
    assert row.descriptor == [
        "Parameter Unit",
        "Description",
        "Range or Values",
        "Command Option",
    ]
    assert row.row_fields["parameter_unit"] == "filter parameter 4"
    assert row.row_fields["description"] == "4th parameter determining which trajectories are kept"
    assert row.row_fields["range_or_values"] == "none, posy, posz"
    assert row.row_fields["command_option"] == "-L"
    assert row.table_title == "The following table lists the parameters of the module 'filter'."
    assert "Command Option: -L" in row.content


def test_multiple_table_rows():
    md = """
# VITESS Module Filter

| Parameter Unit | Description | Command Option |
| --- | --- | --- |
| parameter 1 | first parameter | -A |
| parameter 2 | second parameter | -B |
"""

    chunks = parse_markdown_document(md, source_file="filter.md")
    table_chunks = [chunk for chunk in chunks if chunk.chunk_type == "table"]

    assert len(table_chunks) == 2
    assert table_chunks[0].row_fields["command_option"] == "-A"
    assert table_chunks[1].row_fields["command_option"] == "-B"


def test_code_block_is_marked_as_code():
    md = '''
# Module

```python
print("hello")
```
'''

    chunks = parse_markdown_document(md, source_file="code.md")

    assert len(chunks) == 1
    assert chunks[0].chunk_type == "text"
    assert chunks[0].metadata.is_code_block is True
    assert 'print("hello")' in chunks[0].content


def test_display_math_block_is_an_equation_chunk():
    md = r"""
# VITESS Module Capture Flux

## Capture flux

One does not get the real flux but the integral

$$
\Phi_{capture} = \int \phi(\lambda) \frac{\lambda}{\lambda_{ref}} d\lambda
$$

This integral is calculated in the module.
"""

    chunks = parse_markdown_document(md, source_file="capture_flux.md")

    assert [chunk.chunk_type for chunk in chunks] == ["text", "equation", "text"]
    equation = chunks[1]
    assert equation.content == (
        r"\Phi_{capture} = \int \phi(\lambda) \frac{\lambda}{\lambda_{ref}} d\lambda"
    )
    assert equation.metadata.module == "VITESS Module Capture Flux"
    assert equation.metadata.section == "Capture flux"
    assert chunks[0].content == "One does not get the real flux but the integral"
    assert chunks[2].content == "This integral is calculated in the module."


def test_inline_math_stays_in_its_text_chunk():
    md = """
# VITESS Module Guide

Each plane is described by $ax + by + cz + d = 0$ as an equation of first order.
"""

    chunks = parse_markdown_document(md, source_file="guide.md")

    assert len(chunks) == 1
    assert chunks[0].chunk_type == "text"
    assert "$ax + by + cz + d = 0$" in chunks[0].content
