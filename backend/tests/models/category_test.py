from uuid import uuid4

from app.models.category import Category


def test_category_model_supports_system_and_custom_categories():
    columns = Category.__table__.columns

    assert columns["user_id"].nullable is True
    assert columns["is_system"].nullable is False
    assert "ck_categories_kind" in {c.name for c in Category.__table__.constraints}


def test_category_model_can_represent_system_category():
    category = Category(
        id=uuid4(), user_id=None, name="Food", kind="expense",
        is_system=True,
    )

    assert category.user_id is None
    assert category.is_system is True
