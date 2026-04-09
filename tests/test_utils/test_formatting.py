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
    # Single-key dict: no comma in JSON → no CSV quoting needed
    data = [{"name": "test", "meta": {"key": "val"}}]
    result = format_tabular(data)
    lines = result.strip().split("\n")
    assert lines[1] == 'test,{"key": "val"}'


def test_format_tabular_nested_dict_with_comma():
    # Multi-key dict: JSON contains comma → must be CSV-quoted
    data = [{"name": "test", "meta": {"a": 1, "b": 2}}]
    result = format_tabular(data)
    lines = result.strip().split("\n")
    assert lines[1] == 'test,"{""a"": 1, ""b"": 2}"'


def test_format_tabular_nested_list_csv_quoted():
    data = [{"name": "x", "tags": ["a", "b"]}]
    result = format_tabular(data)
    lines = result.strip().split("\n")
    # list serialized as JSON contains comma → must be quoted
    assert lines[1] == 'x,"[""a"", ""b""]"'
