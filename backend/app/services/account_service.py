
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Account
from app.schemas.account import AccountCreate, AccountUpdate


def create_account(
    db: Session,
    user_id: UUID,
    account_data: AccountCreate,
) -> Account:
    """
    Create an account for the authenticated user.

    We receive user_id from the authentication dependency,
    NOT from the request body.

    This prevents clients from creating accounts for other users.
    """

    account = Account(
        user_id=user_id,
        name=account_data.name.strip(),
        account_type=account_data.account_type,
        currency=account_data.currency,
        opening_balance=account_data.opening_balance,
    )

    # Add the object to the current database transaction.
    db.add(account)

    try:
        # Persist the account.
        db.commit()

        # Refresh retrieves database-generated values such as
        # created_at and updated_at.
        db.refresh(account)

    except Exception:
        # A failed SQLAlchemy transaction must be rolled back
        # before the Session can be used again.
        db.rollback()
        raise

    return account


def get_accounts(
    db: Session,
    user_id: UUID,
    active_only: bool = True,
) -> list[Account]:
    """
    Return accounts belonging to the authenticated user.

    active_only=True:
        Return only accounts that are currently active.

    active_only=False:
        Return active and archived accounts.
    """

    statement = select(Account).where(
        Account.user_id == user_id
    )

    if active_only:
        statement = statement.where(
            Account.is_active.is_(True)
        )

    # Sorting gives the client deterministic results.
    statement = statement.order_by(Account.created_at.desc())

    return list(db.scalars(statement).all())


def get_account_by_id(
    db: Session,
    user_id: UUID,
    account_id: UUID,
) -> Account | None:
    """
    Retrieve one account owned by the authenticated user.

    Notice that we filter by BOTH account_id and user_id.

    If an account exists but belongs to someone else,
    this function returns None.
    """

    statement = select(Account).where(
        Account.id == account_id,
        Account.user_id == user_id,
    )

    return db.scalar(statement)


def update_account(
    db: Session,
    user_id: UUID,
    account_id: UUID,
    account_data: AccountUpdate,
) -> Account | None:
    """
    Update an account's editable fields.

    We use exclude_unset=True so omitted fields are not changed.
    """

    account = get_account_by_id(
        db=db,
        user_id=user_id,
        account_id=account_id,
    )

    if account is None or not account.is_active:
        return None

    # Example:
    # {"name": "My New Savings Account"}
    #
    # Only fields actually supplied by the client are included.
    update_data = account_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if field == "name" and value is not None:
            value = value.strip()

        setattr(account, field, value)

    try:
        db.commit()
        db.refresh(account)

    except Exception:
        db.rollback()
        raise

    return account


def archive_account(
    db: Session,
    user_id: UUID,
    account_id: UUID,
) -> bool:
    """
    Archive an account instead of permanently deleting it.

    Why?

    Historical transactions must remain associated with
    their original accounts.

    We therefore set is_active=False rather than deleting
    the database row.
    """

    account = get_account_by_id(
        db=db,
        user_id=user_id,
        account_id=account_id,
    )

    if account is None or not account.is_active:
        return False

    account.is_active = False

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return True
