import pytest
from unittest.mock import MagicMock
from uuid import UUID

from app.services import csv_transaction_service as csv_service


USER_ID = UUID("df674e14-6782-4f98-a39d-a2703c108e3c")
ACCOUNT_ID = UUID("53ef8f22-c27a-4d51-acfe-0fc0b92b7a03")

HEADER = (
    "account_id,type,amount,currency,description,transaction_date,"
    "category_id,merchant,notes"
)
VALID_ROW = (
    f"{ACCOUNT_ID},expense,250.50,INR,CSV validation test,2026-11-07,,,"
)


def make_csv(*rows: str, header: str = HEADER) -> str:
    return "\n".join([header, *rows])


def make_db() -> MagicMock:
    return MagicMock()


def assert_rejected_without_writes(db: MagicMock, csv_text: str) -> list[dict]:
    with pytest.raises(csv_service.CSVImportValidationError) as exc_info:
        csv_service.import_transactions_from_csv(db, USER_ID, csv_text)

    assert db.add_all.call_count == 0
    assert db.commit.call_count == 0
    return exc_info.value.errors


def test_rejects_csv_without_header():
    db = make_db()

    errors = assert_rejected_without_writes(db, "")

    assert errors == [
        {"row": 1, "errors": ["CSV header row is missing."]}
    ]


def test_rejects_header_only_csv_without_transaction_rows():
    db = make_db()

    errors = assert_rejected_without_writes(db, HEADER)

    assert errors == [
        {"row": 1, "errors": ["CSV contains no transaction rows."]}
    ]


def test_rejects_duplicate_headers():
    db = make_db()
    duplicate_header = HEADER + ",type"

    errors = assert_rejected_without_writes(
        db,
        make_csv(VALID_ROW, header=duplicate_header),
    )

    assert errors == [
        {"row": 1, "errors": ["CSV contains duplicate column names."]}
    ]


def test_rejects_missing_required_headers():
    db = make_db()
    incomplete_header = "account_id,type,amount,currency,description"

    errors = assert_rejected_without_writes(
        db,
        make_csv(
            f"{ACCOUNT_ID},expense,250.50,INR,Missing date",
            header=incomplete_header,
        ),
    )

    assert errors[0]["row"] == 1
    assert any("Missing required columns: transaction_date." in item for item in errors[0]["errors"])


def test_rejects_unsupported_headers():
    db = make_db()
    unsupported_header = HEADER + ",unexpected_column"

    errors = assert_rejected_without_writes(
        db,
        make_csv(VALID_ROW + ",not-allowed", header=unsupported_header),
    )

    assert errors[0]["row"] == 1
    assert any("Unsupported columns: unexpected_column." in item for item in errors[0]["errors"])


@pytest.mark.parametrize(
    ("invalid_value", "expected_error"),
    [
        ("refund", "type: Input should be 'income' or 'expense'"),
        ("0", "amount: Input should be greater than 0"),
        ("not-a-date", "transaction_date:"),
        ("not-a-uuid", "account_id:"),
    ],
)
def test_rejects_invalid_transaction_fields(invalid_value: str, expected_error: str, monkeypatch):
    db = make_db()
    monkeypatch.setattr(csv_service, "validate_transaction_references", lambda **kwargs: None)

    fields = VALID_ROW.split(",")
    if invalid_value in {"refund", "0", "not-a-date"}:
        index = {"refund": 1, "0": 2, "not-a-date": 5}[invalid_value]
        fields[index] = invalid_value
    else:
        fields[0] = invalid_value

    errors = assert_rejected_without_writes(db, make_csv(",".join(fields)))

    assert errors[0]["row"] == 2
    assert any(error.startswith(expected_error) for error in errors[0]["errors"])


def test_rejects_row_when_account_or_category_reference_is_invalid(monkeypatch):
    db = make_db()

    def reject_reference(**kwargs):
        raise ValueError("Account not found or inactive.")

    monkeypatch.setattr(csv_service, "validate_transaction_references", reject_reference)

    errors = assert_rejected_without_writes(db, make_csv(VALID_ROW))

    assert errors == [
        {"row": 2, "errors": ["Account not found or inactive."]}
    ]


def test_rejects_entire_file_when_any_row_is_invalid(monkeypatch):
    db = make_db()
    monkeypatch.setattr(csv_service, "validate_transaction_references", lambda **kwargs: None)

    invalid_row = VALID_ROW.replace(",expense,", ",refund,")
    errors = assert_rejected_without_writes(
        db,
        make_csv(VALID_ROW, invalid_row),
    )

    assert len(errors) == 1
    assert errors[0]["row"] == 3
    assert any("type: Input should be 'income' or 'expense'" in item for item in errors[0]["errors"])


def test_rejects_row_with_more_values_than_header(monkeypatch):
    db = make_db()
    monkeypatch.setattr(csv_service, "validate_transaction_references", lambda **kwargs: None)

    errors = assert_rejected_without_writes(
        db,
        make_csv(VALID_ROW + ",unexpected-extra-value"),
    )

    assert errors == [
        {"row": 2, "errors": ["Row contains more values than the header."]}
    ]
