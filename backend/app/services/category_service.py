
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import Category
from app.schemas.category import CategoryCreate, CategoryUpdate


def create_category(
    db: Session,
    user_id: UUID,
    category_data: CategoryCreate,
) -> Category:
    """
    Create a custom category for the authenticated user.

    System categories are shared and seeded separately.

    Duplicate categories with the same name and kind
    are not allowed for the same user.
    """

    # Check whether the user already has a category with
    # the same name and type, ignoring letter casing.
    existing_category = db.scalar(
        select(Category).where(
            Category.user_id == user_id,
            Category.kind == category_data.kind,
            func.lower(Category.name) == category_data.name.lower(),
        )
    )

    if existing_category:
        raise ValueError(
            "A category with this name and type already exists."
        )

    # Create a custom category.
    category = Category(
        user_id=user_id,
        name=category_data.name,
        kind=category_data.kind,
        icon=category_data.icon,
        color=category_data.color,
        is_system=False,
    )

    try:
        db.add(category)
        db.commit()
        db.refresh(category)

        return category

    except Exception:
        db.rollback()
        raise


def get_categories(
    db: Session,
    user_id: UUID,
    category_kind: str | None = None,
    include_system: bool = True,
) -> list[Category]:
    """
    Return system categories and the authenticated user's
    custom categories.

    System categories have user_id=None and is_system=True.
    Custom categories belong to an individual user.
    """

    # A user can see:
    # 1. Shared system categories.
    # 2. Categories created by that user.
    query = select(Category).where(
        or_(
            Category.user_id == user_id,
            Category.is_system.is_(True),
        )
    )

    # Apply optional income/expense filter.
    if category_kind is not None:
        query = query.where(Category.kind == category_kind)

    # Exclude system categories when explicitly requested.
    if not include_system:
        query = query.where(Category.is_system.is_(False))

    # Return categories in a predictable order.
    query = query.order_by(
        Category.kind.asc(),
        Category.name.asc(),
    )

    return list(db.scalars(query).all())


def get_category_by_id(
    db: Session,
    user_id: UUID,
    category_id: UUID,
) -> Category | None:
    """
    Retrieve a category if it is either:
    - A shared system category.
    - A custom category belonging to the authenticated user.

    Categories belonging to other users are never returned.
    """

    return db.scalar(
        select(Category).where(
            Category.id == category_id,
            or_(
                Category.user_id == user_id,
                Category.is_system.is_(True),
            ),
        )
    )


def update_category(
    db: Session,
    user_id: UUID,
    category_id: UUID,
    category_data: CategoryUpdate,
) -> Category | None:
    """
    Update a custom category.

    System categories cannot be modified.

    Only name, icon, and color can be updated.
    Category kind remains unchanged.
    """

    # Retrieve only a custom category owned by this user.
    category = db.scalar(
        select(Category).where(
            Category.id == category_id,
            Category.user_id == user_id,
            Category.is_system.is_(False),
        )
    )

    if category is None:
        return None

    # Extract only fields explicitly supplied in the PATCH request.
    update_data = category_data.model_dump(exclude_unset=True)

    # Reject requests that contain no changes.
    if not update_data:
        raise ValueError("At least one field must be provided.")

    # A category name cannot be NULL.
    # An omitted name is different from an explicitly null name.
    if "name" in update_data and update_data["name"] is None:
        raise ValueError("Category name cannot be null.")

    # Check for duplicate names if the name is changing.
    new_name = update_data.get("name")

    if new_name is not None:
        existing_category = db.scalar(
            select(Category).where(
                Category.user_id == user_id,
                Category.kind == category.kind,
                Category.id != category_id,
                func.lower(Category.name) == new_name.lower(),
            )
        )

        if existing_category:
            raise ValueError(
                "A category with this name and type already exists."
            )

    # Apply only the supplied fields.
    for field, value in update_data.items():
        setattr(category, field, value)

    try:
        db.commit()
        db.refresh(category)

        return category

    except Exception:
        db.rollback()
        raise


def delete_category(
    db: Session,
    user_id: UUID,
    category_id: UUID,
) -> bool:
    """
    Delete a custom category.

    System categories are protected.

    Existing transactions referencing this category will
    have category_id set to NULL because the database
    foreign key uses ON DELETE SET NULL.
    """

    # Only retrieve a custom category owned by this user.
    category = db.scalar(
        select(Category).where(
            Category.id == category_id,
            Category.user_id == user_id,
            Category.is_system.is_(False),
        )
    )

    if category is None:
        return False

    try:
        db.delete(category)
        db.commit()

        return True

    except Exception:
        db.rollback()
        raise
