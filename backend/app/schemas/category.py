from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


# Categories are classified into two groups.
CategoryKind = Literal["income", "expense"]


class CategoryCreate(BaseModel):
    """
    Request schema for creating a custom category.

    Users can create their own income or expense categories.

    System categories cannot be created through this endpoint.
    They will be inserted through the database seeding process.
    """

    # Category display name.
    name: str = Field(
        min_length=2,
        max_length=100,
    )

    # Determines whether this category is for income or expense.
    kind: CategoryKind

    # Optional icon identifier, for example: shopping-cart.
    icon: str | None = Field(
        default=None,
        max_length=50,
    )

    # Optional hexadecimal color, for example: #FF5733.
    color: str | None = Field(
        default=None,
        max_length=7,
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        """Trim whitespace and reject empty category names."""
        value = value.strip()

        if not value:
            raise ValueError("Category name cannot be empty.")

        return value

    @field_validator("icon")
    @classmethod
    def validate_icon(cls, value: str | None) -> str | None:
        """Normalize optional icon identifiers."""
        if value is not None:
            value = value.strip()

            if not value:
                return None

        return value

    @field_validator("color", mode="before")
    @classmethod
    def validate_color(cls, value: str | None) -> str | None:
        """Trim and validate colors in the hexadecimal format #RRGGBB."""
        if value is not None:
            value = value.strip()

            if not value:
                return None

            if (
                len(value) != 7
                or not value.startswith("#")
                or any(
                    character not in "0123456789abcdefABCDEF"
                    for character in value[1:]
                )
            ):
                raise ValueError(
                    "Color must be a valid hexadecimal color, "
                    "for example #FF5733."
                )

            return value.upper()

        return value


class CategoryUpdate(BaseModel):
    """
    Request schema for updating a custom category.

    Only name, icon, and color can be modified.

    Category kind is intentionally immutable to avoid
    changing the classification of existing transactions.
    """

    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    icon: str | None = Field(
        default=None,
        max_length=50,
    )

    color: str | None = Field(
        default=None,
        max_length=7,
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is not None:
            value = value.strip()

            if not value:
                raise ValueError("Category name cannot be empty.")

        return value

    @field_validator("icon")
    @classmethod
    def validate_icon(cls, value: str | None) -> str | None:
        if value is not None:
            value = value.strip()

            if not value:
                return None

        return value

    @field_validator("color", mode="before")
    @classmethod
    def validate_color(cls, value: str | None) -> str | None:
        if value is not None:
            value = value.strip()

            if not value:
                return None

            if (
                len(value) != 7
                or not value.startswith("#")
                or any(
                    character not in "0123456789abcdefABCDEF"
                    for character in value[1:]
                )
            ):
                raise ValueError(
                    "Color must be a valid hexadecimal color, "
                    "for example #FF5733."
                )

            return value.upper()

        return value


class CategoryResponse(BaseModel):
    """
    Response schema for category information.

    Supports conversion directly from SQLAlchemy models.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID | None

    name: str
    kind: CategoryKind

    icon: str | None
    color: str | None

    is_system: bool

    created_at: datetime
    updated_at: datetime
