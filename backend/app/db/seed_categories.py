from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models import Category


# Default categories available to every SpendWise user.
#
# Each entry contains:
# (name, kind, icon, color)
#
# Icons use Lucide-style kebab-case identifiers.
DEFAULT_SYSTEM_CATEGORIES = [
    # --------------------------------------------------
    # EXPENSE CATEGORIES
    # --------------------------------------------------
    ("Food & Dining", "expense", "utensils", "#F97316"),
    ("Groceries", "expense", "shopping-basket", "#84CC16"),
    ("Transportation", "expense", "car", "#3B82F6"),
    ("Shopping", "expense", "shopping-bag", "#EC4899"),
    ("Entertainment", "expense", "clapperboard", "#A855F7"),
    ("Bills & Utilities", "expense", "receipt", "#EAB308"),
    ("Healthcare", "expense", "heart-pulse", "#EF4444"),
    ("Education", "expense", "graduation-cap", "#6366F1"),
    ("Travel", "expense", "plane", "#06B6D4"),
    ("Rent", "expense", "house", "#8B5CF6"),
    ("Personal Care", "expense", "sparkles", "#D946EF"),
    ("Other Expense", "expense", "wallet", "#64748B"),

    # --------------------------------------------------
    # INCOME CATEGORIES
    # --------------------------------------------------
    ("Salary", "income", "briefcase-business", "#22C55E"),
    ("Freelance", "income", "laptop", "#14B8A6"),
    ("Business", "income", "building-2", "#0D9488"),
    ("Investments", "income", "trending-up", "#10B981"),
    ("Interest", "income", "percent", "#84CC16"),
    ("Gifts", "income", "gift", "#F472B6"),
    ("Other Income", "income", "wallet", "#64748B"),
]


def seed_system_categories(db: Session) -> int:
    """
    Insert missing default system categories.

    This function is idempotent:
    running it multiple times will not create duplicate
    system categories with the same name and type.

    Returns:
        Number of newly inserted categories.
    """

    try:
        # Fetch existing system categories.
        existing_categories = db.scalars(
            select(Category).where(
                Category.is_system.is_(True),
                Category.user_id.is_(None),
            )
        ).all()

        # Build a lookup set using lowercase names.
        # This prevents duplicates caused by letter casing.
        existing_keys = {
            (category.name.strip().casefold(), category.kind)
            for category in existing_categories
        }

        categories_to_insert = []

        # Check every predefined category.
        for name, kind, icon, color in DEFAULT_SYSTEM_CATEGORIES:

            # A category is uniquely identified by its
            # normalized name and transaction kind.
            category_key = (name.casefold(), kind)

            if category_key in existing_keys:
                continue

            # Create a shared system category.
            category = Category(
                user_id=None,
                name=name,
                kind=kind,
                icon=icon,
                color=color,
                is_system=True,
            )

            categories_to_insert.append(category)

            # Also add the key locally to prevent duplicates
            # within the same seed operation.
            existing_keys.add(category_key)

        # Insert all missing categories in one transaction.
        if categories_to_insert:
            db.add_all(categories_to_insert)
            db.commit()

        return len(categories_to_insert)

    except Exception:
        db.rollback()
        raise


def main():
    """
    Command-line entry point for category seeding.

    Creates a database session, executes the seeder,
    and closes the session afterward.
    """

    db = SessionLocal()

    try:
        inserted_count = seed_system_categories(db)

        print(
            f"System category seeding completed. "
            f"{inserted_count} new categories inserted."
        )

    except Exception as error:
        print(f"Category seeding failed: {error}")
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()
