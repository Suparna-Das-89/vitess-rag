from vitess_rag.retrieval import (
    build_context,
    detect_ambiguity,
    extract_command_option,
    extract_module_hint,
    normalize_text,
    rerank_results,
)


def test_normalize_text():
    assert normalize_text("  Hello   WORLD  ") == "hello world"


def test_extract_command_option():
    assert extract_command_option("what does -z mean?") == "-z"
    assert extract_command_option("no option here") is None


def test_extract_module_hint():
    metas = [
        {
            "module": "VITESS Module Filter",
            "section": "",
            "subsection": "",
            "subsubsection": "",
            "source_file": "filter.md",
            "path": "VITESS Module Filter",
        }
    ]

    assert extract_module_hint("tell me about filter", metas) == "filter"


def test_rerank_results_boosts_exact_command_option():
    docs = [
        "Module: Other | Row: Command Option: -A",
        "Module: Filter | Row: Command Option: -L",
    ]

    metas = [
        {
            "module": "Other",
            "section": "",
            "subsection": "",
            "subsubsection": "",
            "source_file": "other.md",
            "path": "Other",
            "chunk_type": "table",
            "row_command_option": "-A",
        },
        {
            "module": "Filter",
            "section": "",
            "subsection": "",
            "subsubsection": "",
            "source_file": "filter.md",
            "path": "Filter",
            "chunk_type": "table",
            "row_command_option": "-L",
        },
    ]

    ranked = rerank_results("what does -L mean?", docs, metas)

    assert ranked[0][1]["row_command_option"] == "-L"


def test_detect_ambiguity_for_same_option_in_multiple_modules():
    ranked = [
        (
            10,
            {
                "module": "Module A",
                "row_command_option": "-L",
                "row_parameter_unit": "parameter A",
                "row_description": "description A",
            },
            "doc A",
        ),
        (
            9,
            {
                "module": "Module B",
                "row_command_option": "-L",
                "row_parameter_unit": "parameter B",
                "row_description": "description B",
            },
            "doc B",
        ),
    ]

    ambiguity = detect_ambiguity("what does -L mean?", ranked)

    assert ambiguity is not None
    assert "Module A" in ambiguity
    assert "Module B" in ambiguity


def test_build_context_contains_metadata_and_content():
    top_hits = [
        (
            12,
            {
                "module": "Filter",
                "section": "Parameters",
                "subsection": "",
                "subsubsection": "",
                "chunk_type": "table",
                "row_parameter_unit": "filter parameter 4",
                "row_command_option": "-L",
                "row_description": "keeps trajectories",
                "table_title": "Filter parameters",
                "table_descriptor": "Parameter Unit | Description | Command Option",
                "source_file": "filter.md",
                "path": "Filter > Parameters",
            },
            "Module: Filter | Row: Command Option: -L",
        )
    ]

    context = build_context(top_hits)

    assert "Filter" in context
    assert "-L" in context
    assert "keeps trajectories" in context
    assert "Module: Filter | Row: Command Option: -L" in context
