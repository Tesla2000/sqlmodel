import pytest
from pydantic import BaseModel, HttpUrl, ValidationError
from sqlmodel import Field, SQLModel, create_engine
from typing import Optional


def test_required_httpurl(clear_sqlmodel) -> None:
    class Product(BaseModel):
        url: HttpUrl

    class StoredProduct(Product, SQLModel, table=True):
        id: int = Field(primary_key=True, default=None)

    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    with pytest.raises(ValidationError):
        StoredProduct(id=1)


def test_required_field_validation_multiple_fields(clear_sqlmodel) -> None:
    class Product(BaseModel):
        name: str
        description: str
        price: float

    class StoredProduct(Product, SQLModel, table=True):
        id: int = Field(primary_key=True, default=None)

    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    # Missing all inherited required fields
    with pytest.raises(ValidationError) as exc_info:
        StoredProduct(id=1)
    assert len(exc_info.value.errors()) == 3

    # Missing some inherited required fields
    with pytest.raises(ValidationError) as exc_info:
        StoredProduct(id=1, name="Widget")
    assert len(exc_info.value.errors()) == 2

    # All required fields provided
    sp = StoredProduct(id=1, name="Widget", description="A widget", price=9.99)
    assert sp.name == "Widget"
    assert sp.description == "A widget"
    assert sp.price == 9.99


def test_optional_inherited_fields(clear_sqlmodel) -> None:
    class Product(BaseModel):
        name: str
        tags: Optional[str] = None

    class StoredProduct(Product, SQLModel, table=True):
        id: int = Field(primary_key=True, default=None)

    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    # Optional field can be omitted
    sp = StoredProduct(id=1, name="Widget")
    assert sp.name == "Widget"
    assert sp.tags is None

    # Required field cannot be omitted
    with pytest.raises(ValidationError):
        StoredProduct(id=1)


def test_inherited_fields_with_defaults(clear_sqlmodel) -> None:
    class Product(BaseModel):
        name: str
        category: str = "general"

    class StoredProduct(Product, SQLModel, table=True):
        id: int = Field(primary_key=True, default=None)

    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    # Field with default can be omitted
    sp = StoredProduct(id=1, name="Widget")
    assert sp.name == "Widget"
    assert sp.category == "general"

    # Required field cannot be omitted
    with pytest.raises(ValidationError):
        StoredProduct(id=1, category="special")


def test_mixed_required_and_optional_inheritance(clear_sqlmodel) -> None:
    class BaseEntity(BaseModel):
        created_by: str
        updated_by: Optional[str] = None

    class Product(BaseEntity):
        name: str
        sku: str = "unknown"

    class StoredProduct(Product, SQLModel, table=True):
        id: int = Field(primary_key=True, default=None)

    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    # Missing required inherited fields
    with pytest.raises(ValidationError) as exc_info:
        StoredProduct(id=1, name="Widget")
    errors = exc_info.value.errors()
    assert any(e["loc"] == ("created_by",) for e in errors)

    # All required fields provided
    sp = StoredProduct(
        id=1,
        created_by="admin",
        name="Widget",
    )
    assert sp.created_by == "admin"
    assert sp.updated_by is None
    assert sp.name == "Widget"
    assert sp.sku == "unknown"
