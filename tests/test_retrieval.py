from vitess_rag.retrieval import extract_command_option, normalize_text


def test_normalize_text():
    assert normalize_text("  Hello   WORLD  ") == "hello world"


def test_extract_command_option():
    assert extract_command_option("what does -z mean?") == "-z"
    assert extract_command_option("no option here") is None
