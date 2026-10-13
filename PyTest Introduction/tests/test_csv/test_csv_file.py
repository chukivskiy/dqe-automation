import pytest
import re


def test_file_not_empty(read_file):
    df = read_file
    assert not df.empty

@pytest.mark.validate_csv
@pytest.mark.xfail(reason="Known issue: duplicate rows exist")
def test_duplicates(read_file):
    assert not read_file.duplicated().any()

@pytest.mark.validate_csv
def test_validate_schema(read_file, validate_schema):
    actual_schema = read_file.columns.tolist()
    expected_schema = ["id", "name", "age", "email", "is_active"]
    validate_schema(actual_schema, expected_schema)


@pytest.mark.validate_csv
@pytest.mark.skip(reason="Age validation is temporarily skipped")
def test_age_column_valid(read_file):
    assert read_file["age"].between(0, 100).all()

@pytest.mark.validate_csv
def test_email_column_valid(read_file):
    email_pattern = re.compile(
        r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    )

    assert read_file["email"].apply(
        lambda email: isinstance(email, str)
                      and bool(email_pattern.fullmatch(email))
    ).all()


@pytest.mark.parametrize(
    "id, is_active",
    [
        (1, False),
        (2, True)
    ]
)
def test_active_players(read_file, id, is_active):
    rows = read_file.loc[read_file["id"] == id, "is_active"]

    assert len(rows) == 1
    assert bool(rows.iloc[0]) == is_active


def test_active_player(read_file):
    rows = read_file.loc[read_file["id"] == 2, "is_active"]

    assert len(rows) == 1
    assert bool(rows.iloc[0]) is True