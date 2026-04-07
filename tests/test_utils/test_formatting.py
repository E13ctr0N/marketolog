from marketolog.utils.formatting import format_tabular


def test_format_tabular_basic():
    data = [
        {"keyword": "таск трекер", "volume": 1200, "position": 8},
        {"keyword": "управление задачами", "volume": 800, "position": 14},
    ]
    result = format_tabular(data)
    lines = result.strip().split("\n")
    assert lines[0] == "keyword,volume,position"
    assert lines[1] == "таск трекер,1200,8"
    assert lines[2] == "управление задачами,800,14"


def test_format_tabular_empty():
    assert format_tabular([]) == ""


def test_format_tabular_single_row():
    data = [{"name": "test", "value": 42}]
    result = format_tabular(data)
    assert result.strip() == "name,value\ntest,42"


def test_format_tabular_with_commas_in_values():
    data = [{"title": "Hello, world", "count": 1}]
    result = format_tabular(data)
    lines = result.strip().split("\n")
    assert lines[1] == '"Hello, world",1'


def test_format_tabular_with_none():
    data = [{"a": 1, "b": None}]
    result = format_tabular(data)
    lines = result.strip().split("\n")
    assert lines[1] == "1,"


def test_format_tabular_with_nested_dict():
    data = [{"name": "test", "meta": {"key": "val"}}]
    result = format_tabular(data)
    lines = result.strip().split("\n")
    assert '{"key": "val"}' in lines[1]
