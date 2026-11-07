import pytest

from app.services.csv_transaction_service import CSVImportValidationError, _clean_optional


def test_csv_import_validation_error_exposes_row_errors():
    errors = [{"row": 2, "errors": ["invalid amount"]}]

    error = CSVImportValidationError(errors)

    assert error.errors == errors
    assert "No transactions were imported" in str(error)


@pytest.mark.parametrize(
    ("value", "expected"),
    [(None, None), ("", None), ("   ", None), (" merchant ", "merchant")],
)
def test_clean_optional_normalizes_empty_and_non_empty_values(value, expected):
    assert _clean_optional(value) == expected
