
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.models import Account, Category, Transaction
from app.schemas.transaction import TransactionCreate, TransactionUpdate


def validate_transaction_references(
    db: Session,
    user_id: UUID,
    account_id: UUID,
    category_id: UUID | None,
    transaction_type: str,
    currency: str,
) -> None:
    """
    Validate the account and category before creating or updating
    a transaction.

    Security rules:
    1. Account must belong to the authenticated user.
    2. Account must be active.
    3. Category must belong to the user or be a system category.
    4. Category kind must match income/expense.
    5. Transaction currency must match account currency.
    """

    # ---------------------------------------------------------
    # 1. Validate account ownership and active status.
    # ---------------------------------------------------------

    account_statement = select(Account).where(
        Account.id == account_id,
        Account.user_id == user_id,
        Account.is_active.is_(True),
    )

    account = db.scalar(account_statement)

    if account is None:
        raise ValueError("Account not found or inactive.")

    # ---------------------------------------------------------
    # 2. Validate transaction currency.
    # ---------------------------------------------------------

    if account.currency != currency:
        raise ValueError(
            f"Transaction currency must match account currency ({account.currency})."
        )

    # ---------------------------------------------------------
    # 3. Validate category if one was provided.
    # ---------------------------------------------------------

    if category_id is None:
        return

    # A category is valid if:
    # - It belongs to the authenticated user, OR
    # - It is a shared system category with no user_id.

    category_statement = select(Category).where(
        Category.id == category_id,
        or_(
            Category.user_id == user_id,
            and_(
                Category.user_id.is_(None),
                Category.is_system.is_(True),
            ),
        ),
    )

    category = db.scalar(category_statement)

    if category is None:
        raise ValueError("Category not found.")

    # Income transactions must use income categories.
    # Expense transactions must use expense categories.

    if category.kind != transaction_type:
        raise ValueError(
            f"Category type must match transaction type ({transaction_type})."
        )


def create_transaction(
    db: Session,
    user_id: UUID,
    transaction_data: TransactionCreate,
) -> Transaction:
    """
    Create an income or expense transaction.

    user_id is supplied by the authentication dependency,
    never by the request body.
    """

    # Validate account and category before inserting anything.
    validate_transaction_references(
        db=db,
        user_id=user_id,
        account_id=transaction_data.account_id,
        category_id=transaction_data.category_id,
        transaction_type=transaction_data.type,
        currency=transaction_data.currency,
    )

    transaction = Transaction(
        user_id=user_id,
        account_id=transaction_data.account_id,
        category_id=transaction_data.category_id,
        type=transaction_data.type,
        amount=transaction_data.amount,
        currency=transaction_data.currency,
        description=transaction_data.description,
        merchant=transaction_data.merchant,
        transaction_date=transaction_data.transaction_date,
        notes=transaction_data.notes,
    )

    db.add(transaction)

    try:
        db.commit()
        db.refresh(transaction)

    except Exception:
        db.rollback()
        raise

    return transaction


def get_transaction_by_id(
    db: Session,
    user_id: UUID,
    transaction_id: UUID,
) -> Transaction | None:
    """
    Retrieve a transaction belonging to the authenticated user.

    Filtering by both IDs prevents cross-user data access.
    """

    statement = select(Transaction).where(
        Transaction.id == transaction_id,
        Transaction.user_id == user_id,
    )

    return db.scalar(statement)


def get_transactions(
    db: Session,
    user_id: UUID,
    transaction_type: str | None = None,
    account_id: UUID | None = None,
    category_id: UUID | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[Transaction], int]:
    """
    Retrieve transactions belonging to one user.

    Supports:
    - Filtering by income/expense.
    - Filtering by account.
    - Filtering by category.
    - Filtering by date range.
    - Pagination.

    Returns:
        A tuple containing:
        1. List of transactions.
        2. Total matching transaction count.
    """

    # Every query starts with the authenticated user's ID.
    statement = select(Transaction).where(
        Transaction.user_id == user_id
    )

    # Apply optional filters.

    if transaction_type is not None:
        statement = statement.where(
            Transaction.type == transaction_type
        )

    if account_id is not None:
        statement = statement.where(
            Transaction.account_id == account_id
        )

    if category_id is not None:
        statement = statement.where(
            Transaction.category_id == category_id
        )

    if start_date is not None:
        statement = statement.where(
            Transaction.transaction_date >= start_date
        )

    if end_date is not None:
        statement = statement.where(
            Transaction.transaction_date <= end_date
        )

    # Count matching records before pagination.
    count_statement = (
        select(func.count())
        .select_from(Transaction)
        .where(Transaction.user_id == user_id)
    )

    # Apply the same filters to the count query.
    if transaction_type is not None:
        count_statement = count_statement.where(
            Transaction.type == transaction_type
        )

    if account_id is not None:
        count_statement = count_statement.where(
            Transaction.account_id == account_id
        )

    if category_id is not None:
        count_statement = count_statement.where(
            Transaction.category_id == category_id
        )

    if start_date is not None:
        count_statement = count_statement.where(
            Transaction.transaction_date >= start_date
        )

    if end_date is not None:
        count_statement = count_statement.where(
            Transaction.transaction_date <= end_date
        )

    total = db.scalar(count_statement) or 0

    # Newest transactions appear first.
    statement = statement.order_by(
        Transaction.transaction_date.desc(),
        Transaction.created_at.desc(),
    )

    # Apply pagination.
    statement = statement.offset(offset).limit(limit)

    transactions = list(db.scalars(statement).all())

    return transactions, total


def update_transaction(
    db: Session,
    user_id: UUID,
    transaction_id: UUID,
    transaction_data: TransactionUpdate,
) -> Transaction | None:
    """
    Partially update an existing transaction.

    Only fields explicitly supplied by the client are updated.
    All references and financial constraints are revalidated.
    """

    transaction = get_transaction_by_id(
        db=db,
        user_id=user_id,
        transaction_id=transaction_id,
    )

    if transaction is None:
        return None

    # Exclude fields that were not provided in the PATCH request.
    update_data = transaction_data.model_dump(exclude_unset=True)

    # These database fields cannot be set to NULL.
    non_nullable_fields = {
        "account_id",
        "type",
        "amount",
        "currency",
        "description",
        "transaction_date",
    }

    for field in non_nullable_fields:
        if field in update_data and update_data[field] is None:
            raise ValueError(f"{field} cannot be null.")

    # Determine the final values after applying the PATCH.
    # We validate the complete resulting transaction, not
    # merely the individual fields supplied by the client.

    new_account_id = update_data.get(
        "account_id", transaction.account_id
    )

    new_category_id = update_data.get(
        "category_id", transaction.category_id
    )

    new_type = update_data.get(
        "type", transaction.type
    )

    new_currency = update_data.get(
        "currency", transaction.currency
    )

    # Validate the resulting account/category combination.
    validate_transaction_references(
        db=db,
        user_id=user_id,
        account_id=new_account_id,
        category_id=new_category_id,
        transaction_type=new_type,
        currency=new_currency,
    )

    # Update only the fields supplied by the client.
    for field, value in update_data.items():
        setattr(transaction, field, value)

    try:
        db.commit()
        db.refresh(transaction)

    except Exception:
        db.rollback()
        raise

    return transaction
