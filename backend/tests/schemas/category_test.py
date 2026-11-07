import pytest
from pydantic import ValidationError

from app.schemas.category import CategoryCreate, CategoryUpdate


def test_category_create_trims_name_and_normalizes_optional_fields():
    category = CategoryCreate(
        name="  Food  ", kind="expense", icon="  ",
        color=" #ff5733 ",
    )

    assert category.name == "Food"
    assert category.icon is None
    assert category.color == "#FF5733"


@pytest.mark.parametrize("color", ["red", "#FFF", "FF5733", "#GGGGGG"])
def test_category_create_rejects_invalid_color(color):
    with pytest.raises(ValidationError):
        CategoryCreate(name="Food", kind="expense", color=color)


def test_category_create_rejects_blank_name():
    with pytest.raises(ValidationError):
        CategoryCreate(name="   ", kind="expense")


def test_category_update_normalizes_fields():
    update = CategoryUpdate(name="  Travel ", icon=" ")
    assert update.name == "Travel"
    assert update.icon is None
