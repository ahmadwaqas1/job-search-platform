from app.services.salary_service import _percentiles_from_rows


def test_percentiles_from_rows_basic():
    rows = [(50_000, 60_000), (70_000, 80_000), (90_000, 100_000), (40_000, None), (None, 120_000)]
    result = _percentiles_from_rows(rows)
    assert result is not None
    assert result["sample_size"] == 5
    assert result["p10"] <= result["median"] <= result["p90"]


def test_percentiles_from_rows_insufficient_data():
    assert _percentiles_from_rows([(50_000, 60_000)]) is None
    assert _percentiles_from_rows([]) is None


def test_percentiles_from_rows_ignores_fully_empty_rows():
    rows = [(None, None), (50_000, 60_000), (70_000, 80_000), (90_000, 100_000)]
    result = _percentiles_from_rows(rows)
    assert result["sample_size"] == 3
